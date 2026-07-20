from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings


is_sqlite = settings.database_url.startswith("sqlite")
is_in_memory_sqlite = settings.database_url in {"sqlite://", "sqlite:///:memory:"}
connect_args = {"check_same_thread": False} if is_sqlite else {}
engine_options = {
    "connect_args": connect_args,
    "pool_pre_ping": True,
    **({"poolclass": StaticPool} if is_in_memory_sqlite else {}),
}
engine = create_engine(settings.database_url, **engine_options)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def initialize_database() -> None:
    Base.metadata.create_all(bind=engine)

    if not settings.database_url.startswith("sqlite"):
        return

    with engine.begin() as connection:
        inspector = inspect(connection)
        table_columns = {
            table: {column["name"] for column in inspector.get_columns(table)}
            for table in inspector.get_table_names()
        }

        def add_column(table: str, column: str, definition: str) -> None:
            if column not in table_columns.get(table, set()):
                connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {definition}"))

        add_column("leads", "metadata", "metadata JSON NOT NULL DEFAULT '{}'")
        add_column("leads", "assigned_to", "assigned_to VARCHAR(255)")
        add_column("emails", "tracking_token", "tracking_token VARCHAR(255)")
        add_column("emails", "opened_at", "opened_at DATETIME")
        add_column("emails", "clicked_at", "clicked_at DATETIME")
        add_column("emails", "open_count", "open_count INTEGER NOT NULL DEFAULT 0")
        add_column("emails", "click_count", "click_count INTEGER NOT NULL DEFAULT 0")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
