import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models.product import Base

def get_engine(db_path: str):
    # Ensure the directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Create SQLite URL
    db_url = f"sqlite:///{db_path}"
    
    engine = create_engine(
        db_url, connect_args={"check_same_thread": False}
    )
    return engine

def init_db(db_path: str):
    engine = get_engine(db_path)
    Base.metadata.create_all(bind=engine)
    return engine

def get_session_local(engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)
