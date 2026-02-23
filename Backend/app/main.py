from fastapi import FastAPI
from app.core.database import Base, engine

app = FastAPI()

# Create tables on startup (simple way for MVP)
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
