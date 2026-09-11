from pathlib import Path
from datetime import datetime
import shutil

here = Path(__file__).resolve().parent
db = here / "rescueai.db"
if not db.exists():
    raise SystemExit(f"Database not found: {db}")

out = here / f"rescueai_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
shutil.copy2(db, out)
print(out)
