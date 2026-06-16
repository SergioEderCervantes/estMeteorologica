# Backend — Estación Meteorológica

El backend tiene **dos servicios independientes** que deben correr al mismo tiempo:

| Servicio | Qué hace |
|---|---|
| **FastAPI** | Expone la API REST que consume el frontend |
| **Serial Reader** | Lee el ESP32 por USB y alimenta la base de datos |

---

## Requisitos previos

- Python 3.11 o superior instalado
- Dependencias instaladas: `pip install -r requirements.txt`

---

## Servicio 1 — FastAPI

Abre una terminal en la carpeta `backend/` y ejecuta:

```
uvicorn app.main:app --reload
```

El servidor queda corriendo en `http://localhost:8000`.

### Verificar que funciona

Abre el navegador en:

```
http://localhost:8000/docs
```

Vas a ver la documentación interactiva (Swagger UI) con todos los endpoints disponibles. Para probar que la API responde puedes hacer click en `GET /readings/latest` → **Try it out** → **Execute**. Si no hay lecturas todavía devuelve 404, eso es normal.

---

## Servicio 2 — Serial Reader (ESP32)

### Antes de encenderlo

1. **Conecta el ESP32** a la PC por USB.
2. **Cierra el Serial Monitor de Arduino IDE** si lo tienes abierto — no pueden compartir el mismo puerto al mismo tiempo o el lector va a fallar.
3. Confirma el puerto: abre el **Administrador de dispositivos** (clic derecho en el ícono de Windows → Administrador de dispositivos) y busca la sección **Puertos (COM y LPT)**. Deberías ver algo como `Silicon Labs CP210x USB to UART Bridge (COM3)`. El puerto fue **COM3** la última vez.

### Encenderlo

Abre **otra terminal** (diferente a la de FastAPI) en la carpeta `backend/` y ejecuta:

```
python serial_runner.py --port COM3 --station esp32-01
```

Si tu puerto es diferente al COM3, cambia el número. Por ejemplo: `--port COM4`.

### Verificar que funciona

En la misma terminal deberías ver las lecturas llegando en tiempo real, una por segundo, así:

```
[serial] conectado a COM3 @ 115200
{"reading_id": "...", "station_id": "esp32-01", "temperature": {"celsius": 24.5, ...}, ...}
{"reading_id": "...", "station_id": "esp32-01", "temperature": {"celsius": 24.6, ...}, ...}
```

Para confirmar que llegan a la base de datos, ve a la pestaña del navegador con los docs de FastAPI (`http://localhost:8000/docs`) y ejecuta `GET /readings/latest` — ahora sí debe devolver la lectura más reciente.

---

## Apagar los servicios

En cada terminal presiona `Ctrl + C`.
