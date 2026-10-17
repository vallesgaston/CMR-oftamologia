from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def guardar(db: Session, mensaje_conflicto: str = "Conflicto con datos existentes") -> None:
    """Commit que convierte violaciones de unicidad en HTTP 409."""
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=mensaje_conflicto)


def obtener_o_404(db: Session, modelo, id_: int):
    obj = db.get(modelo, id_)
    if obj is None:
        raise HTTPException(status_code=404, detail=f"{modelo.__name__} no encontrado")
    return obj
