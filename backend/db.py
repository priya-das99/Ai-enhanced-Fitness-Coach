import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Import settings
try:
    from app.config import settings
except ImportError:
    # Fallback for direct execution
    DATABASE_URL = os.getenv('DATABASE_URL', '')
    DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'mood_capture.db')
    if DATABASE_URL:
        engine = create_engine(DATABASE_URL)
    else:
        engine = create_engine(
            f"sqlite:///{DATABASE_PATH}",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

if 'settings' in locals():
    if settings.DATABASE_URL:
        engine = create_engine(settings.DATABASE_URL)
    else:
        engine = create_engine(
            f"sqlite:///{settings.DATABASE_PATH}",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
else:
    # Use the fallback engine
    pass

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Session:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Legacy function for backward compatibility
def get_connection():
    """Legacy SQLite connection for existing code"""
    if 'sqlite' in str(engine.url):
        import sqlite3
        conn = sqlite3.connect(str(engine.url).replace('sqlite:///', ''), timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn
    else:
        raise NotImplementedError("Legacy connection not supported for PostgreSQL")

def init_db():
    """Initialize the database"""
    from app.models import user  # Import models to create tables
    from sqlalchemy import MetaData
    from app.models.user import Base

    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully!")

if __name__ == '__main__':
    init_db()