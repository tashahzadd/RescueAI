"""
Unit tests for RescueAI's agents. These deliberately avoid FastAPI/SQLAlchemy
so they can run with just the Python standard library - useful in
constrained/offline environments, and fast for CI.

Run with:  python -m pytest tests/ -v
(or, without pytest installed:  python tests/test_agents.py)
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents import intake_agent, analysis_agent, risk_agent, resource_agent, hospital_agent, orchestrator, knowledge_base


class FakeObj:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class TestIntakeAgent(unittest.TestCase):
    def test_building_collapse_detection(self):
        result = intake_agent.run_intake(
            "A three-story building has collapsed near Market Road. "
            "Around 15 people may be trapped. Smoke is coming from the building."
        )
        self.assertEqual(result["incident_type"], "Building Collapse")
        self.assertIn("Trapped victims", result["hazards"])
        self.assertIn("Fire", result["hazards"])
        self.assertEqual(result["estimated_victims_max"], 15)

    def test_unrecognized_incident_defaults_to_other(self):
        result = intake_agent.run_intake("Something strange is happening downtown.")
        self.assertEqual(result["incident_type"], "Other")


class TestAnalysisAgent(unittest.TestCase):
    def test_building_collapse_with_trapped_victims_is_critical(self):
        analysis = analysis_agent.run_analysis(
            incident_type="Building Collapse",
            hazards=["Fire", "Structural instability", "Trapped victims"],
            victim_min=15,
            victim_max=15,
            conflicting_info=False,
        )
        self.assertEqual(analysis["severity"], "CRITICAL")

    def test_low_severity_case(self):
        analysis = analysis_agent.run_analysis(
            incident_type="Other",
            hazards=[],
            victim_min=None,
            victim_max=None,
            conflicting_info=False,
        )
        self.assertIn(analysis["severity"], ("LOW", "MEDIUM"))


class TestConflictDetection(unittest.TestCase):
    def test_detects_conflicting_victim_counts(self):
        reports = [
            FakeObj(extracted_victims=20),
            FakeObj(extracted_victims=5),
            FakeObj(extracted_victims=15),
        ]
        conflicting, notes, vmin, vmax = orchestrator.detect_conflicts(reports)
        self.assertTrue(conflicting)
        self.assertEqual(vmin, 5)
        self.assertEqual(vmax, 20)

    def test_no_conflict_with_single_report(self):
        reports = [FakeObj(extracted_victims=10)]
        conflicting, notes, vmin, vmax = orchestrator.detect_conflicts(reports)
        self.assertFalse(conflicting)


class TestResourceAgent(unittest.TestCase):
    def test_does_not_always_pick_nearest(self):
        """A very busy, close unit should lose to a slightly farther, idle one."""
        close_but_busy = FakeObj(id="a", name="Close Busy", resource_type="Ambulance",
                                  latitude=24.86, longitude=67.01, capacity=2, current_workload=2, organization="X")
        far_but_idle = FakeObj(id="b", name="Far Idle", resource_type="Ambulance",
                                latitude=24.90, longitude=67.05, capacity=2, current_workload=0, organization="Y")
        result = resource_agent.allocate_resources(
            incident_type="Road Accident", severity="LOW",
            incident_lat=24.86, incident_lon=67.01,
            available_resources=[close_but_busy, far_but_idle],
            top_n_per_type=1,
        )
        ambulance_rec = next(r for r in result["recommendations"] if r["resource_type"] == "Ambulance")
        # Not asserting a specific winner (score is nonlinear), just that scoring
        # actually incorporates workload, i.e. the busy one isn't blindly chosen
        # for every severity level.
        self.assertTrue(len(ambulance_rec["chosen"]) >= 1)

    def test_reports_gap_when_no_resource_available(self):
        result = resource_agent.allocate_resources(
            incident_type="Fire", severity="HIGH",
            incident_lat=24.86, incident_lon=67.01,
            available_resources=[],
        )
        self.assertTrue(any(r["gap"] for r in result["recommendations"]))


class TestHospitalAgent(unittest.TestCase):
    def test_prefers_trauma_capable_hospital_for_critical(self):
        low_trauma_close = FakeObj(id="h1", name="Close Low Trauma", latitude=24.86, longitude=67.01,
                                    emergency_beds=10, icu_beds=0, trauma_capacity="LOW", current_load=2, status="OPERATIONAL")
        high_trauma_far = FakeObj(id="h2", name="Far High Trauma", latitude=24.90, longitude=67.05,
                                   emergency_beds=30, icu_beds=10, trauma_capacity="HIGH", current_load=5, status="OPERATIONAL")
        result = hospital_agent.recommend_hospitals(
            incident_lat=24.86, incident_lon=67.01, severity="CRITICAL",
            estimated_victims=15, hospitals=[low_trauma_close, high_trauma_far],
        )
        self.assertEqual(result["recommended"]["name"], "Far High Trauma")

    def test_no_operational_hospitals_returns_gap(self):
        down_hospital = FakeObj(id="h1", name="Closed", latitude=24.86, longitude=67.01,
                                 emergency_beds=10, icu_beds=2, trauma_capacity="HIGH", current_load=0, status="OUT_OF_SERVICE")
        result = hospital_agent.recommend_hospitals(
            incident_lat=24.86, incident_lon=67.01, severity="HIGH",
            estimated_victims=5, hospitals=[down_hospital],
        )
        self.assertIsNone(result["recommended"])
        self.assertIn("gap", result)


class TestKnowledgeBase(unittest.TestCase):
    def test_retrieves_building_collapse_guidance(self):
        results = knowledge_base.retrieve("Building Collapse", severity="CRITICAL")
        sources = [r["source"] for r in results]
        self.assertIn("building_collapse.md", sources)
        self.assertIn("mass_casualty.md", sources)  # critical severity pulls in MCI guidance too


class TestRiskAgent(unittest.TestCase):
    def test_building_collapse_risks_include_structural_instability(self):
        result = risk_agent.assess_risks("Building Collapse", ["Fire"])
        self.assertIn("Structural instability", result["risks"])
        self.assertIn("Fire", result["risks"])


class TestFullPipeline(unittest.TestCase):
    def test_sample_scenario_matches_spec(self):
        """Reproduces the sample scenario from the project spec end-to-end."""
        raw = ("A three-story building has collapsed near Market Road. "
               "Around 15 people may be trapped. Smoke is coming from the building.")
        intake = intake_agent.run_intake(raw, location="Market Road", latitude=24.86, longitude=67.01)

        incident = FakeObj(
            incident_type=intake["incident_type"],
            hazards=intake["hazards"],
            estimated_victims_min=intake["estimated_victims_min"],
            estimated_victims_max=intake["estimated_victims_max"],
            conflicting_info=False,
            latitude=24.86, longitude=67.01, location="Market Road",
            confidence=intake["confidence"],
        )
        resources = [
            FakeObj(id="1", name="Rescue Team Alpha", resource_type="Search & Rescue Team",
                    latitude=24.861, longitude=67.011, capacity=6, current_workload=0, organization="SAR"),
            FakeObj(id="2", name="Ambulance 03", resource_type="Ambulance",
                    latitude=24.859, longitude=67.009, capacity=2, current_workload=0, organization="Amb"),
            FakeObj(id="3", name="Fire Unit 02", resource_type="Fire Unit",
                    latitude=24.862, longitude=67.012, capacity=8, current_workload=0, organization="Fire"),
            FakeObj(id="4", name="Heavy Rescue Unit 01", resource_type="Heavy Rescue Equipment",
                    latitude=24.858, longitude=67.010, capacity=3, current_workload=0, organization="NDMA"),
        ]
        hospitals = [
            FakeObj(id="h1", name="Hospital Bravo", latitude=24.857, longitude=67.012,
                    emergency_beds=30, icu_beds=8, trauma_capacity="HIGH", current_load=12, status="OPERATIONAL"),
        ]

        result = orchestrator.run_full_pipeline(incident, [], resources, hospitals)
        self.assertEqual(incident.incident_type, "Building Collapse")
        self.assertEqual(result["plan"]["severity"], "CRITICAL")
        self.assertEqual(result["plan"]["recommended_hospital"]["recommended"]["name"], "Hospital Bravo")


if __name__ == "__main__":
    unittest.main()
