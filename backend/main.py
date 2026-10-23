from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db
from routers import auth

app = FastAPI()
app.include_router(auth.router)


@app.get("/")
def home():
    return {"message": "SnippetHub API is running"}


@app.get("/health/db")
def db_health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"database": "connected"}