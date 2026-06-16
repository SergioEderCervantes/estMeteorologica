# Backend — Estación Meteorológica

El backend tiene **tres servicios independientes** que deben correr al mismo tiempo:

| Servicio | Qué hace |
|---|---|
| **FastAPI** | Expone la API REST que consume el frontend |
| **Serial Reader** | Lee el ESP32 por USB y alimenta la base de datos |
| **Blynk Runner** | Toma la última lectura de la DB y la empuja a Blynk IoT |

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

## Servicio 3 — Blynk Runner

Empuja la última lectura de la base de datos a Blynk IoT cada 5 segundos.

### Antes de encenderlo

Asegúrate de que el archivo `.env` existe en la carpeta `backend/` con el token de Blynk:

```
BLYNK_TOKEN=tu_token_aqui
```

El archivo ya debería estar creado. Si no existe, créalo manualmente — no se sube al repositorio por seguridad.

### Encenderlo

Abre **otra terminal** en la carpeta `backend/` y ejecuta:

```
python blynk_runner.py
```

Si quieres cambiar el intervalo de envío (por defecto 5 segundos):

```
python blynk_runner.py --interval 10
```

### Verificar que funciona

En la terminal deberías ver una línea por cada envío exitoso:

```
[blynk] iniciado — intervalo 5.0s
[blynk] enviado — 2024-01-15T10:30:00+00:00 | T:24.5°C H:65.0%
[blynk] enviado — 2024-01-15T10:30:05+00:00 | T:24.6°C H:65.1%
```

Si aún no hay lecturas en la base de datos (el Serial Reader no ha corrido todavía), verás:

```
[blynk] sin lecturas en la DB, esperando...
```

Eso es normal — en cuanto el Serial Reader empiece a recibir datos del ESP32, el Blynk Runner los va a empujar automáticamente.

---

## Apagar los servicios

En cada terminal presiona `Ctrl + C`.
