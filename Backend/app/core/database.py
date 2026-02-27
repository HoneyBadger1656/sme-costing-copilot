import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

# Database configuration - support both SQLite and PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Fallback to SQLite for development
    DB_DIR = Path(__file__).parent.parent.parent.parent
    DB_PATH = DB_DIR / "test.db"
    DATABASE_URL = f"sqlite:///{DB_PATH}"

print(f"[DATABASE] Using: {DATABASE_URL}")

# Configure engine based on database type
if "sqlite" in DATABASE_URL:
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
