from db import fetch_one


def main():
    result = fetch_one("SELECT NOW() AS current_time;")
    print("PostgreSQL connection successful.")
    print(f"Current database time: {result['current_time']}")


if __name__ == "__main__":
    main()