from src.app.database.models import Base
from src.app.database.db import engine

def reset_db():
    print("WARNING: Deleting ALL application data...")
    Base.metadata.drop_all(bind=engine)
    print("Database is now empty.")