from fastapi import APIRouter, HTTPException
from app.adapter import RawReading, StationReading, normalize
from app import storage

router = APIRouter()


@router.post("/readings", status_code=201, response_model=StationReading)
def create_reading(raw: RawReading):
    """Recibe datos crudos del ESP32, los normaliza y los guarda."""
    reading = normalize(raw)
    storage.save(reading)
    return reading


@router.get("/readings", response_model=list[StationReading])
def list_readings(station_id: str | None = None, limit: int = 100):
    """Devuelve las últimas lecturas. Filtra por station_id si se provee."""
    return storage.get_all(station_id=station_id, limit=limit)


@router.get("/readings/latest", response_model=StationReading)
def latest_reading(station_id: str | None = None):
    """Devuelve la lectura más reciente."""
    reading = storage.get_latest(station_id=station_id)
    if not reading:
        raise HTTPException(status_code=404, detail="No hay lecturas registradas")
    return reading


@router.get("/readings/{reading_id}", response_model=StationReading)
def get_reading(reading_id: str):
    """Devuelve una lectura específica por su UUID."""
    reading = storage.get_by_id(reading_id)
    if not reading:
        raise HTTPException(status_code=404, detail="Lectura no encontrada")
    return reading
