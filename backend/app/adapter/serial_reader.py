import time
import serial
from serial import SerialException

from app.adapter import RawReading, normalize

# Espeja los umbrales de ejecutor.cpp
_TEMP_MAX = 30.0
_HUM_MAX = 80.0
_LUZ_UMBRAL = 400
_LLUVIA_UMBRAL = 2000

_RETRY_DELAY = 5  # segundos entre intentos de reconexión


def parse_line(line: str, station_id: str) -> RawReading | None:
    """Convierte una línea serial del ESP32 en un RawReading.

    Formato normal:   "temp,hum,luz_raw,lluvia_raw"
    Formato error:    "ERROR_DHT,0,0,0"
    Devuelve None si la línea no es parseable.
    """
    line = line.strip()
    if not line:
        return None

    parts = line.split(",")
    if len(parts) != 4:
        return None

    if parts[0] == "ERROR_DHT":
        return RawReading(
            station_id=station_id,
            temperature_c=0.0,
            humidity_pct=0.0,
            light_adc=0,
            rain_adc=0,
            fan=False,
            led=False,
            buzzer=False,
            dht11_status="error",
        )

    try:
        temp = float(parts[0])
        hum = float(parts[1])
        luz = int(parts[2])
        lluvia = int(parts[3])
    except ValueError:
        return None

    return RawReading(
        station_id=station_id,
        temperature_c=temp,
        humidity_pct=hum,
        light_adc=luz,
        rain_adc=lluvia,
        fan=temp > _TEMP_MAX or hum > _HUM_MAX,
        led=luz < _LUZ_UMBRAL,
        buzzer=lluvia < _LLUVIA_UMBRAL,
    )


def read_serial(port: str, station_id: str, baud: int = 115200, interval: float = 1.0):
    """Generador que yield dicts normalizados leyendo el puerto serial indefinidamente.

    Reconecta automáticamente si el puerto se desconecta.
    Solo emite una lectura cada `interval` segundos; el resto se descarta.
    """
    last_yield = 0.0
    while True:
        try:
            with serial.Serial(port, baud, timeout=2) as ser:
                print(f"[serial] conectado a {port} @ {baud}")
                while True:
                    raw_line = ser.readline().decode("utf-8", errors="replace")
                    reading_raw = parse_line(raw_line, station_id)
                    if reading_raw is None:
                        continue
                    if reading_raw.dht11_status == "error":
                        print("[serial] ERROR_DHT — lectura descartada")
                        continue
                    now = time.monotonic()
                    if now - last_yield < interval:
                        continue
                    last_yield = now
                    yield normalize(reading_raw)
        except SerialException as exc:
            print(f"[serial] error: {exc}. Reintentando en {_RETRY_DELAY}s…")
            print(f"[serial] verifica que el puerto {port!r} esté disponible "
                  f"(Administrador de dispositivos > Puertos COM y LPT)")
            time.sleep(_RETRY_DELAY)
