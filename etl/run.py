from etl.load import apply_schema, ensure_database, load_all
from etl.train import train_and_forecast


def main() -> None:
    print("== ETL analisis-mercado ==")
    ensure_database()
    apply_schema()
    load_all()
    train_and_forecast()
    print("Listo")


if __name__ == "__main__":
    main()
