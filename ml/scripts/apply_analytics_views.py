from pathlib import Path

from db import execute_query, fetch_one


ROOT_DIR = Path(__file__).resolve().parents[2]
SQL_PATH = ROOT_DIR / "database" / "analytics_views.sql"

VIEWS = [
    "vw_daily_radiation_summary",
    "vw_hourly_radiation_summary",
    "vw_location_anomaly_summary",
    "vw_model_performance",
    "vw_latest_anomalies",
]


def apply_analytics_views():
    if not SQL_PATH.exists():
        raise FileNotFoundError(f"SQL file not found: {SQL_PATH}")

    sql = SQL_PATH.read_text(encoding="utf-8")

    print("Applying analytics views...")
    execute_query(sql)
    print("Analytics views applied successfully.")


def validate_views():
    print("")
    print("Validating created views...")

    for view_name in VIEWS:
        row = fetch_one(
            f"""
            SELECT COUNT(*) AS total_rows
            FROM {view_name};
            """
        )

        total_rows = int(row["total_rows"] or 0)
        print(f"{view_name}: {total_rows} rows")


def main():
    apply_analytics_views()
    validate_views()

    print("")
    print("DWH / analytics layer is ready.")


if __name__ == "__main__":
    main()