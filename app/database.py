import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL","postgresql+psycopg://postgres:postgres@localhost:5432/parking"
)


engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind = engine)

class Base(DeclarativeBase):
    pass

