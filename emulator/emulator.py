"""Эмулятор Wi-Fi сенсоров: каждый виртуальный сенсор работает в своем потоке."""
import json
import math
import random
import threading
import urllib.error
import urllib.request
from pathlib import Path

API_URL = "http://localhost:8000/telemetry/batch"
SEND_INTERVAL = 2.0   # секунд между отправками пачек
RSSI_AT_1M = -40      # уровень сигнала на расстоянии 1 метр
PATH_LOSS_N = 3.0     # коэффициент затухания (в помещении 2.5 - 4)
BROADCAST = "FF:FF:FF:FF:FF:FF"

# Легитимная точка доступа.
CORP_AP = {
    "ssid": "CorpWiFi",
    "mac": "AA:BB:CC:DD:EE:FF",
    "encryption": "WPA2",
    "channel": 6,
    "pos": (2.0, 6.0),
}

# Клиентские устройства. Потом их MAC нужно добавить в белый список устройств.
CLIENTS = [
    {"mac": "11:22:33:44:55:66", "pos": (3.0, 2.0)},
    {"mac": "11:22:33:44:55:77", "pos": (7.0, 5.0)},
    {"mac": "11:22:33:44:55:88", "pos": (9.0, 7.0)},
]


def rssi_for(sensor_pos, emitter_pos) -> int:
    """Уровень сигнала по расстоянию + небольшой случайный шум."""
    distance = max(math.dist(sensor_pos, emitter_pos), 0.5)
    rssi = RSSI_AT_1M - 10 * PATH_LOSS_N * math.log10(distance)
    rssi += random.gauss(0, 2)
    return max(-100, min(-1, round(rssi)))


def build_events(sensor_pos) -> list[dict]:
    """Формирует пачку событий, которые «услышал» сенсор."""
    events = [
        {
            "src_mac": CORP_AP["mac"],
            "dst_mac": BROADCAST,
            "rssi": rssi_for(sensor_pos, CORP_AP["pos"]),
            "ssid": CORP_AP["ssid"],
            "channel": CORP_AP["channel"],
            "encryption": CORP_AP["encryption"],
            "frame_type": "Beacon",
            "vendor_ie": {"vendor": "ExampleVendor"},
        }
    ]
    for client in CLIENTS:
        if random.random() < 0.6:
            events.append(
                {
                    "src_mac": client["mac"],
                    "dst_mac": BROADCAST,
                    "rssi": rssi_for(sensor_pos, client["pos"]),
                    "ssid": CORP_AP["ssid"],
                    "channel": CORP_AP["channel"],
                    "frame_type": "Probe Request",
                }
            )
    return events


def send_batch(sensor: dict, events: list[dict]) -> None:
    body = json.dumps({"events": events}).encode("utf-8")
    request = urllib.request.Request(
        API_URL,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json", "X-API-Key": sensor["api_key"]},
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            print(f"[{sensor['name']}] отправлено {len(events)} событий, ответ {response.status}")
    except urllib.error.HTTPError as e:
        print(f"[{sensor['name']}] ошибка сервера: {e.code} {e.read().decode()[:200]}")
    except urllib.error.URLError as e:
        print(f"[{sensor['name']}] сервер недоступен: {e.reason}")


def run_sensor(sensor: dict, stop: threading.Event) -> None:
    pos = (sensor["x"], sensor["y"])
    while not stop.is_set():
        send_batch(sensor, build_events(pos))
        stop.wait(SEND_INTERVAL)  # пауза, которую можно прервать по Ctrl+C


def main() -> None:
    config_path = Path(__file__).parent / "sensors.json"
    sensors = json.loads(config_path.read_text(encoding="utf-8"))

    stop = threading.Event()
    threads = [
        threading.Thread(target=run_sensor, args=(s, stop), daemon=True) for s in sensors
    ]
    for t in threads:
        t.start()
    print(f"Запущено сенсоров: {len(threads)}. Остановить: Ctrl+C")

    try:
        while True:
            stop.wait(1)
    except KeyboardInterrupt:
        print("Останавливаю эмулятор...")
        stop.set()
        for t in threads:
            t.join(timeout=3)


if __name__ == "__main__":
    main()