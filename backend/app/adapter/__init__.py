import uuid
from datetime import datetime, timezone
from pydantic import BaseModel

TEMP_MIN, TEMP_MAX = -20.0, 50.0
RAIN_THRESHOLD = 2000  # ADC 0-4095; por debajo de esto se considera lluvia (sensor conduce más al mojarse)


class RawReading(BaseModel):
    """Payload exacto que manda el ESP32."""
    station_id: str
    temperature_c: float
    humidity_pct: float
    light_adc: int       # valor ADC 0-4095 del LDR
    rain_adc: int        # valor ADC 0-4095 del FC-37
    fan: bool
    led: bool
    buzzer: bool
    dht11_status: str = "ok"   # "ok" | "error" | "timeout"
    ldr_status: str = "ok"     # "ok" | "error"
    fc37_status: str = "ok"    # "ok" | "error"


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def _normalize(v, lo, hi):
    return (v - lo) / (hi - lo)


def _heat_index(t: float, h: float) -> float:
    # Fórmula de Steadman; solo aplica con t>27°C y h>40%
    if t < 27 or h < 40:
        return round(t, 2)
    hi = (
        -8.78469475556
        + 1.61139411 * t
        + 2.33854883889 * h
        - 0.14611605 * t * h
        - 0.012308094 * t ** 2
        - 0.0164248277778 * h ** 2
        + 0.002211732 * t ** 2 * h
        + 0.00072546 * t * h ** 2
        - 0.000003582 * t ** 2 * h ** 2
    )
    return round(hi, 2)


def _light_label(normalized: float) -> str:
    if normalized < 0.25:
        return "oscuro"
    if normalized < 0.50:
        return "tenue"
    if normalized < 0.75:
        return "moderado"
    return "brillante"


def normalize(raw: RawReading) -> dict:
    temp_c = round(_clamp(raw.temperature_c, TEMP_MIN, TEMP_MAX), 2)
    hum_pct = round(_clamp(raw.humidity_pct, 0.0, 100.0), 2)
    light_norm = round(_normalize(_clamp(raw.light_adc, 0, 4095), 0, 4095), 4)
    rain_norm = round(_normalize(_clamp(raw.rain_adc, 0, 4095), 0, 4095), 4)

    return {
        "reading_id": str(uuid.uuid4()),
        "station_id": raw.station_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "temperature": {
            "celsius": temp_c,
            "normalized": round(_normalize(temp_c, TEMP_MIN, TEMP_MAX), 4),
        },
        "humidity": {
            "percent": hum_pct,
            "normalized": round(_normalize(hum_pct, 0.0, 100.0), 4),
        },
        "heat_index": _heat_index(temp_c, hum_pct),
        "light": {
            "normalized": light_norm,
            "label": _light_label(light_norm),
        },
        "rain": {
            "is_raining": raw.rain_adc < RAIN_THRESHOLD,
            "intensity": rain_norm,
        },
        "actuators": {
            "fan": raw.fan,
            "led": raw.led,
            "buzzer": raw.buzzer,
        },
        "sensor_status": {
            "dht11": raw.dht11_status,
            "ldr": raw.ldr_status,
            "fc37": raw.fc37_status,
        },
    }
