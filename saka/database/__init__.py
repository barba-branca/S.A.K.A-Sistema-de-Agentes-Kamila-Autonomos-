# Transforma 'database' em um submódulo do pacote 'saka'
from .database import Base, engine, SessionLocal
from .models import Trade