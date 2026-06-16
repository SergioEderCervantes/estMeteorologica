"""
Uso:
    python blynk_runner.py [--interval 5]

Lee la última lectura del storage y la empuja a Blynk cada `interval` segundos.
Requiere BLYNK_TOKEN en el archivo .env
"""
import argparse
import os
import time

import requests

from app import storage


_TOKEN = 'k5ZVN7L0t8NpyCz63npAOhMGn-o5NBBm'
_BASE  = f"https://blynk.cloud/external/api/update?token={_TOKEN}"


def _push(pin: str, value) -> None:
    requests.get(f"{_BASE}&{pin}={value}", timeout=5)


def push_reading(reading: dict) -> None:
    temp  = reading["temperature"]
    hum   = reading["humidity"]
    light = reading["light"]
    rain  = reading["rain"]
    act   = reading["actuators"]

    _push("V0", temp["celsius"])
    _push("V1", hum["percent"])
    _push("V2", reading["heat_index"])
    _push("V3", light["normalized"])
    _push("V4", light["label"])
    _push("V5", 1 if rain["is_raining"] else 0)
    _push("V6", rain["intensity"])
    _push("V7", 1 if act["fan"] else 0)
    _push("V8", 1 if act["led"] else 0)
    _push("V9", 1 if act["buzzer"] else 0)


def main():
    parser = argparse.ArgumentParser(description="Pusher de lecturas a Blynk")
    parser.add_argument("--interval", type=float, default=5.0,
                        help="Segundos entre cada envío a Blynk (default: 5)")
    args = parser.parse_args()

    storage.init_db()
    print(f"[blynk] iniciado — intervalo {args.interval}s")

    while True:
        reading = storage.get_latest()
        if reading is None:
            print("[blynk] sin lecturas en la DB, esperando...")
        else:
            push_reading(reading)
            ts = reading["timestamp"]
            temp = reading["temperature"]["celsius"]
            hum  = reading["humidity"]["percent"]
            print(f"[blynk] enviado — {ts} | T:{temp}°C H:{hum}%")

        time.sleep(args.interval)


if __name__ == "__main__":
    main()
