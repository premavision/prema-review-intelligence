from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine

from app.core.config import settings

# Configure database engine with security settings
connect_args: dict[str, object] = {}
if settings.database_url.startswith("sqlite"):
    # SQLite-specific security settings
    connect_args = {
        "check_same_thread": False,
        "timeout": 20.0,  # Connection timeout to prevent hanging
    }
    # In production, consider using WAL mode for better concurrency
    # This should be set via PRAGMA after connection

# Configure engine with connection pooling for better performance and security
# Pool settings help prevent connection exhaustion attacks
engine = create_engine(
    settings.database_url,
    echo=False,
    connect_args=connect_args,
    pool_pre_ping=True,  # Verify connections before using them
    pool_size=5,  # Limit concurrent connections
    max_overflow=10,  # Maximum overflow connections
    pool_recycle=3600,  # Recycle connections after 1 hour
)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


def init_db() -> None:
    SQLModel.metadata.create_all(engine)

