from sqlalchemy import Column, Integer, String, Float, JSON, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from geoalchemy2 import Geometry
from config import Config
import pgvector.sqlalchemy  # Для векторных полей

Base = declarative_base()

class Photo(Base):
    __tablename__ = 'photos'
    
    id = Column(Integer, primary_key=True)
    file_path = Column(String, nullable=False)  # Путь к файлу
    lat = Column(Float)  # Широта
    lon = Column(Float)  # Долгота
    embedding = Column(pgvector.sqlalchemy.Vector(512))  # Векторный эмбеддинг (e.g., от CLIP, размер 512)
    metadata = Column(JSON)  # Дополнительные данные (e.g., объект, нарушение)
    geom = Column(Geometry(geometry_type='POINT', srid=4326))  # PostGIS для geo-индекса

class Task(Base):
    __tablename__ = 'tasks'
    
    id = Column(String, primary_key=True)  # Celery task_id
    status = Column(String)  # PENDING, STARTED, SUCCESS, FAILURE
    result = Column(JSON)  # Результат (координаты, сравнение)

# Инициализация БД (вызвать в app.py)
engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)