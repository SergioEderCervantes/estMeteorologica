"""
Uso:
    python serial_runner.py --port COM3 --station esp32-01
    python serial_runner.py --port COM3 --station esp32-01 --baud 115200

El puerto COM lo puedes ver en: Administrador de dispositivos > Puertos (COM y LPT)
"""
import argparse
import json

from app import storage
from app.adapter.serial_reader import read_serial


def main():
    parser = argparse.ArgumentParser(description="Lector serial del ESP32")
    parser.add_argument("--port", required=True, help="Puerto serial (ej: COM3, COM4)")
    parser.add_argument("--station", required=True, help="ID de la estación (ej: esp32-01)")
    parser.add_argument("--baud", type=int, default=115200, help="Baud rate (default: 115200)")
    args = parser.parse_args()

    storage.init_db()
    print(f"[runner] escuchando {args.port} — station={args.station}")

    try:
        for reading in read_serial(args.port, args.station, args.baud):
            storage.save(reading)
            print(json.dumps(reading, ensure_ascii=False))
    except KeyboardInterrupt:
        print("\n[runner] detenido")


if __name__ == "__main__":
    main()
