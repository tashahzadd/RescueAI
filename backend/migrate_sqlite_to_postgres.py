import argparse
from sqlalchemy import create_engine, MetaData, select
from sqlalchemy.exc import IntegrityError

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--sqlite", default="sqlite:///./rescueai.db")
    p.add_argument("--postgres", required=True)
    args = p.parse_args()

    src = create_engine(args.sqlite)
    dst = create_engine(args.postgres, pool_pre_ping=True)

    src_meta = MetaData()
    src_meta.reflect(bind=src)
    src_meta.create_all(bind=dst)

    dst_meta = MetaData()
    dst_meta.reflect(bind=dst)

    total_inserted = 0
    for s_table in src_meta.sorted_tables:
        name = s_table.name
        if name not in dst_meta.tables:
            print("SKIP:", name)
            continue

        d_table = dst_meta.tables[name]
        with src.connect() as conn:
            rows = [dict(r._mapping) for r in conn.execute(select(s_table))]

        inserted = 0
        for row in rows:
            try:
                with dst.begin() as conn:
                    conn.execute(d_table.insert().values(**row))
                inserted += 1
            except IntegrityError:
                pass

        total_inserted += inserted
        print(f"{name}: source={len(rows)} inserted={inserted}")

    print("Migration complete. Total inserted:", total_inserted)

if __name__ == "__main__":
    main()
