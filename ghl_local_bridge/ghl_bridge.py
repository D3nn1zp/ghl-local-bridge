from __future__ import annotations

import hashlib
import json
import os
import re
import signal
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import paho.mqtt.client as mqtt
from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException, WebDriverException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

OPTIONS_FILE = Path("/data/options.json")
SETUP_FLAG = Path("/data/setup_complete.flag")
DEBUG_DIR = Path("/data/debug")
STOP_EVENT = threading.Event()


@dataclass(frozen=True)
class Settings:
    ghl_url: str
    pin: str
    interval_minutes: int
    device_name: str
    mqtt_topic_prefix: str
    setup_ui: bool
    debug: bool
    enabled_sensors: frozenset[str]
    mqtt_host: str
    mqtt_port: int
    mqtt_username: str
    mqtt_password: str

    @property
    def interval_seconds(self) -> int:
        return self.interval_minutes * 60

    @property
    def state_topic(self) -> str:
        return f"{self.mqtt_topic_prefix}/state"

    @property
    def availability_topic(self) -> str:
        return f"{self.mqtt_topic_prefix}/status"

    @property
    def device_identifier(self) -> str:
        # Zelfde identifier-opbouw als de eerdere versies, zodat entiteiten behouden blijven.
        digest = hashlib.sha1(self.mqtt_topic_prefix.encode("utf-8")).hexdigest()[:12]
        return f"ghl_cloud_bridge_{digest}"


SENSORS: dict[str, dict[str, Any]] = {
    "kh": {
        "name": "KH",
        "labels": ["Actuele waarde", "Current value", "Aktueller Wert"],
        "unit_regex": r"°?dKH",
        "unit": "°dKH",
        "precision": 1,
        "thousands": False,
    },
    "temperature": {
        "name": "Temperatuur",
        "labels": ["Temperatuur 1", "Temperature 1", "Temperatur 1"],
        "unit_regex": r"°C",
        "unit": "°C",
        "precision": 1,
        "thousands": False,
        "device_class": "temperature",
    },
    "density": {
        "name": "Dichtheid zee",
        "labels": ["Geleid.(Zee) 1", "Conduct.(S) 1", "Conduct.(Sea) 1", "Leitw.(Meerw.) 1"],
        "unit_regex": r"kg/L",
        "unit": "kg/L",
        "precision": 4,
        "thousands": False,
    },
    "calcium": {
        "name": "Calcium",
        "labels": ["Calcium", "Kalzium"],
        "unit_regex": r"mg/L",
        "unit": "mg/L",
        "precision": 0,
        "thousands": False,
    },
    "magnesium": {
        "name": "Magnesium",
        "labels": ["Magnesium"],
        "unit_regex": r"mg/L",
        "unit": "mg/L",
        "precision": 0,
        "thousands": True,
    },
    "potassium": {
        "name": "Kalium",
        "labels": ["Kalium", "Potassium"],
        "unit_regex": r"mg/L",
        "unit": "mg/L",
        "precision": 0,
        "thousands": False,
    },
    "sodium": {
        "name": "Natrium",
        "labels": ["Natrium", "Sodium"],
        "unit_regex": r"mg/L",
        "unit": "mg/L",
        "precision": 0,
        "thousands": True,
    },
    "nitrate": {
        "name": "Nitraat",
        "labels": ["Nitraat", "Nitrate", "Nitrat"],
        "unit_regex": r"mg/L",
        "unit": "mg/L",
        "precision": 0,
        "thousands": False,
    },
}


def log(message: str, level: str = "INFO") -> None:
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [{level}] {message}", flush=True)


def normalize_url(value: str) -> str:
    url = value.strip()
    if "://" not in url:
        url = "http://" + url
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise RuntimeError("ghl_url is geen geldig HTTP- of HTTPS-adres.")
    return url.rstrip("/")


def load_settings() -> Settings:
    options = json.loads(OPTIONS_FILE.read_text(encoding="utf-8"))
    pin = str(options.get("ghl_pin", "")).strip()
    if not pin:
        raise RuntimeError("ghl_pin ontbreekt.")

    interval = int(options.get("interval_minutes", 15))
    if interval < 1 or interval > 1440:
        raise RuntimeError("interval_minutes moet tussen 1 en 1440 liggen.")

    topic = str(options.get("mqtt_topic_prefix", "ghl/aquarium")).strip().strip("/")
    if not topic or not re.fullmatch(r"[A-Za-z0-9_./-]+", topic):
        raise RuntimeError("mqtt_topic_prefix bevat ongeldige tekens.")

    mqtt_host = os.getenv("MQTT_HOST", "").strip()
    if not mqtt_host:
        raise RuntimeError("De interne MQTT-service is niet beschikbaar.")

    sensor_options = options.get("sensors", {})
    if not isinstance(sensor_options, dict):
        sensor_options = {}
    # Ontbrekende sensoropties blijven standaard ingeschakeld voor een soepele update vanaf oudere versies.
    enabled_sensors = frozenset(
        key for key in SENSORS if bool(sensor_options.get(key, True))
    )
    if not enabled_sensors:
        raise RuntimeError("Selecteer minimaal één sensor onder 'Sensoren selecteren'.")

    return Settings(
        ghl_url=normalize_url(str(options.get("ghl_url", ""))),
        pin=pin,
        interval_minutes=interval,
        device_name=str(options.get("device_name", "GHL Aquarium")).strip() or "GHL Aquarium",
        mqtt_topic_prefix=topic,
        setup_ui=bool(options.get("setup_ui", True)),
        debug=bool(options.get("debug", False)),
        enabled_sensors=enabled_sensors,
        mqtt_host=mqtt_host,
        mqtt_port=int(os.getenv("MQTT_PORT", "1883")),
        mqtt_username=os.getenv("MQTT_USERNAME", ""),
        mqtt_password=os.getenv("MQTT_PASSWORD", ""),
    )


def attach_browser() -> webdriver.Chrome:
    options = webdriver.ChromeOptions()
    options.add_experimental_option("debuggerAddress", os.getenv("CHROME_REMOTE_DEBUGGING", "127.0.0.1:9222"))
    driver = webdriver.Chrome(service=Service("/usr/bin/chromedriver"), options=options)
    driver.set_page_load_timeout(90)
    return driver


def body_text(driver: webdriver.Chrome) -> str:
    try:
        return driver.find_element(By.TAG_NAME, "body").text
    except Exception:
        return ""


def visible_elements(driver: webdriver.Chrome, by: str, selector: str) -> list[Any]:
    result = []
    try:
        elements = driver.find_elements(by, selector)
    except Exception:
        return result
    for element in elements:
        try:
            if element.is_displayed():
                result.append(element)
        except (StaleElementReferenceException, WebDriverException):
            continue
    return result


def ensure_ghl_tab(driver: webdriver.Chrome, settings: Settings) -> None:
    handles = driver.window_handles
    if not handles:
        driver.execute_cdp_cmd("Target.createTarget", {"url": settings.ghl_url})
        time.sleep(2)
        handles = driver.window_handles
    driver.switch_to.window(handles[0])

    # Houd GHL Connect actief, ook als de zichtbare instelbrowser uit staat.
    try:
        driver.set_window_size(1920, 1080)
        driver.execute_cdp_cmd("Page.bringToFront", {})
        driver.execute_script("window.focus(); if (document.body) document.body.focus();")
    except WebDriverException:
        pass

    current = driver.current_url or ""
    if current.startswith("about:") or current.startswith("chrome:"):
        driver.get(settings.ghl_url)
        time.sleep(4)
    elif SETUP_FLAG.exists() and not current.startswith(settings.ghl_url):
        driver.get(settings.ghl_url)
        time.sleep(4)


def wizard_visible(text: str) -> bool:
    markers = (
        "Initial setup",
        "Select your language first",
        "Would you like to connect the app to a myGHL account",
        "The initial setup is now complete",
        "Done!",
        "Ersteinrichtung",
    )
    return any(marker in text for marker in markers)


def pin_prompt(driver: webdriver.Chrome) -> Any | None:
    for selector in ("input.alert-input", ".alert-wrapper input", "ion-alert input"):
        fields = visible_elements(driver, By.CSS_SELECTOR, selector)
        if fields:
            return fields[0]
    return None


def enter_pin_if_needed(driver: webdriver.Chrome, settings: Settings) -> bool:
    field = pin_prompt(driver)
    if field is None:
        return False
    try:
        field.clear()
        field.send_keys(settings.pin)
        time.sleep(0.5)
        buttons = visible_elements(
            driver,
            By.XPATH,
            "//button[.//span[translate(normalize-space(.), 'ok', 'OK')='OK'] or translate(normalize-space(.), 'ok', 'OK')='OK']",
        )
        if buttons:
            buttons[-1].click()
        else:
            field.send_keys(Keys.ENTER)
        log("Lokale GHL-PIN ingevuld.")
        time.sleep(5)
        return True
    except StaleElementReferenceException:
        # GHL vervangt het PIN-venster direct na een succesvolle bevestiging.
        log("Lokale GHL-PIN bevestigd.")
        time.sleep(5)
        return True
    except Exception as exc:
        log(f"PIN kon niet automatisch worden ingevuld: {exc}", "WARNING")
        return False


def convert_number(raw: str, *, thousands: bool) -> float:
    value = raw.strip().replace(" ", "")
    if thousands:
        value = value.replace(".", "").replace(",", "")
    else:
        if "," in value and "." in value:
            # De laatst gebruikte separator is het decimaalteken.
            if value.rfind(",") > value.rfind("."):
                value = value.replace(".", "").replace(",", ".")
            else:
                value = value.replace(",", "")
        else:
            value = value.replace(",", ".")
    return float(value)


def find_value(text: str, key: str, sensor: dict[str, Any]) -> int | float | None:
    if key == "density":
        match = re.search(r"([0-9]+(?:[.,][0-9]+)?)\s*kg/L", text, re.IGNORECASE)
        if not match:
            return None
        return round(convert_number(match.group(1), thousands=False), sensor["precision"])

    for label in sensor["labels"]:
        pattern = (
            r"([0-9][0-9.,]*)\s*" + sensor["unit_regex"] + r"\s*" + re.escape(label)
        )
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if not match:
            continue
        value = convert_number(match.group(1), thousands=sensor["thousands"])
        if sensor["precision"] == 0:
            return int(round(value))
        return round(value, sensor["precision"])
    return None


def extract_values(
    text: str,
    enabled_sensors: frozenset[str],
) -> tuple[dict[str, int | float], list[str]]:
    values: dict[str, int | float] = {}
    missing: list[str] = []
    for key, sensor in SENSORS.items():
        if key not in enabled_sensors:
            continue
        value = find_value(text, key, sensor)
        if value is None:
            missing.append(key)
        else:
            values[key] = value
    return values, missing


def required_dashboard_cards(enabled_sensors: frozenset[str]) -> list[str]:
    cards: list[str] = []
    if "kh" in enabled_sensors:
        cards.append("KH Director")
    if enabled_sensors.intersection({"temperature", "density"}):
        cards.append("Sensors / Sensoren")
    if enabled_sensors.intersection({"calcium", "magnesium", "potassium", "sodium", "nitrate"}):
        cards.append("ION Director")
    return cards


def wait_for_selected_values(
    driver: webdriver.Chrome,
    enabled_sensors: frozenset[str],
    timeout: int = 180,
) -> tuple[dict[str, int | float], list[str]]:
    """Wacht tot alle geselecteerde dashboardkaarten hun waarden hebben geladen."""
    deadline = time.monotonic() + timeout
    last_missing: list[str] = []

    while time.monotonic() < deadline and not STOP_EVENT.is_set():
        try:
            driver.execute_cdp_cmd("Page.bringToFront", {})
            driver.execute_script("window.focus(); if (document.body) document.body.focus();")
        except WebDriverException:
            pass

        text = body_text(driver)
        values, missing = extract_values(text, enabled_sensors)
        if not missing:
            return values, []
        last_missing = missing
        sleep_interruptible(5)

    text = body_text(driver)
    values, missing = extract_values(text, enabled_sensors)
    return values, missing or last_missing


def create_mqtt_client(settings: Settings) -> mqtt.Client:
    connected = threading.Event()

    def on_connect(client: mqtt.Client, userdata: Any, flags: Any, reason_code: Any, properties: Any) -> None:
        # Paho MQTT 2.x geeft hier een ReasonCode-object door.
        # Vergelijken met 0 is officieel ondersteund; int(reason_code) niet.
        if reason_code == 0:
            connected.set()
        else:
            log(f"MQTT-verbinding geweigerd: {reason_code}", "ERROR")

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="ghl_local_bridge_visible")
    client.on_connect = on_connect
    if settings.mqtt_username:
        client.username_pw_set(settings.mqtt_username, settings.mqtt_password)
    client.will_set(settings.availability_topic, "offline", qos=1, retain=True)
    client.reconnect_delay_set(min_delay=5, max_delay=60)
    client.connect(settings.mqtt_host, settings.mqtt_port, keepalive=60)
    client.loop_start()
    if not connected.wait(15):
        raise RuntimeError("MQTT-verbinding kwam niet tot stand.")
    return client


def publish_discovery(client: mqtt.Client, settings: Settings) -> None:
    device = {
        "identifiers": [settings.device_identifier],
        "name": settings.device_name,
        "manufacturer": "GHL",
        "model": "ProfiLux lokale browserbridge",
    }
    for key, sensor in SENSORS.items():
        topic = f"homeassistant/sensor/ghl_aquarium/{key}/config"
        if key not in settings.enabled_sensors:
            # Leeg retained discoverybericht verwijdert een eerder aangemaakte MQTT-entiteit.
            client.publish(topic, "", qos=1, retain=True).wait_for_publish()
            continue

        payload: dict[str, Any] = {
            "name": sensor["name"],
            "unique_id": f"{settings.device_identifier}_{key}",
            "state_topic": settings.state_topic,
            "value_template": "{{ value_json." + key + " }}",
            "availability_topic": settings.availability_topic,
            "payload_available": "online",
            "payload_not_available": "offline",
            "unit_of_measurement": sensor["unit"],
            "state_class": "measurement",
            "suggested_display_precision": sensor["precision"],
            "device": device,
        }
        if "device_class" in sensor:
            payload["device_class"] = sensor["device_class"]
        client.publish(topic, json.dumps(payload), qos=1, retain=True).wait_for_publish()
    log(
        "Home Assistant MQTT Discovery verzonden voor: "
        + ", ".join(sorted(settings.enabled_sensors))
    )


def publish_values(client: mqtt.Client, settings: Settings, values: dict[str, int | float]) -> None:
    client.publish(settings.state_topic, json.dumps(values, separators=(",", ":")), qos=1, retain=True).wait_for_publish()
    client.publish(settings.availability_topic, "online", qos=1, retain=True).wait_for_publish()
    log("Waarden via MQTT naar Home Assistant verzonden.")


def save_debug(driver: webdriver.Chrome, reason: str) -> None:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    try:
        (DEBUG_DIR / "page.txt").write_text(
            f"Reden: {reason}\nURL: {driver.current_url}\n\n{body_text(driver)}",
            encoding="utf-8",
        )
        driver.save_screenshot(str(DEBUG_DIR / "page.png"))
    except Exception:
        pass


def sleep_interruptible(seconds: int) -> None:
    STOP_EVENT.wait(seconds)


def handle_signal(signum: int, frame: Any) -> None:
    del frame
    log(f"Stopsignaal ontvangen ({signum}).")
    STOP_EVENT.set()


def main() -> None:
    settings = load_settings()
    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    log(f"GHL Local Bridge gestart; uitleesinterval {settings.interval_minutes} minuten.")
    log(f"Lokale GHL: {settings.ghl_url}")
    if settings.setup_ui:
        log("Gebruik Open Web UI voor de eenmalige browserinstelling. Home Assistant Ingress beveiligt de instelbrowser.")
    log("Geselecteerde sensoren: " + ", ".join(sorted(settings.enabled_sensors)))

    mqtt_client = create_mqtt_client(settings)
    publish_discovery(mqtt_client, settings)

    driver: webdriver.Chrome | None = None
    last_setup_log = 0.0

    try:
        while not STOP_EVENT.is_set():
            try:
                if driver is None:
                    log("Verbinden met de blijvende Chromium-sessie...")
                    driver = attach_browser()

                ensure_ghl_tab(driver, settings)
                text = body_text(driver)

                if wizard_visible(text):
                    now = time.monotonic()
                    if now - last_setup_log > 30:
                        log(
                            "Eerste installatie is nog niet afgerond. Open Web UI en kies: taal → NEXT → NO → DONE.",
                            "WARNING",
                        )
                        last_setup_log = now
                    sleep_interruptible(15)
                    continue

                pin_was_entered = enter_pin_if_needed(driver, settings)
                if pin_was_entered:
                    log("Wachten tot de geselecteerde dashboardwaarden zijn geladen...")

                values, missing = wait_for_selected_values(
                    driver,
                    settings.enabled_sensors,
                    timeout=180 if pin_was_entered else 45,
                )
                if missing:
                    now = time.monotonic()
                    if now - last_setup_log > 30:
                        readable = ", ".join(missing)
                        cards = ", ".join(required_dashboard_cards(settings.enabled_sensors))
                        log(
                            "Dashboard bevat nog niet alle geselecteerde waarden. Open Web UI, klik op het potlood "
                            f"en controleer deze kaart(en): {cards}. Ontbrekend: {readable}.",
                            "WARNING",
                        )
                        last_setup_log = now
                    sleep_interruptible(20)
                    continue

                if not SETUP_FLAG.exists():
                    SETUP_FLAG.write_text("ok\n", encoding="utf-8")
                    log("Eenmalige browserinstelling is compleet en blijft in /data bewaard.")

                log("Gevonden waarden: " + ", ".join(f"{k}={v}" for k, v in values.items()))
                publish_values(mqtt_client, settings, values)
                sleep_interruptible(settings.interval_seconds)

            except WebDriverException as exc:
                log(f"Chromium-verbinding verloren: {exc}. Opnieuw verbinden...", "WARNING")
                if driver is not None:
                    try:
                        driver.quit()
                    except Exception:
                        pass
                driver = None
                sleep_interruptible(10)
            except Exception as exc:
                log(f"Uitlezen mislukt: {exc}", "ERROR")
                if driver is not None and settings.debug:
                    save_debug(driver, str(exc))
                sleep_interruptible(30)
    finally:
        try:
            mqtt_client.publish(settings.availability_topic, "offline", qos=1, retain=True)
            time.sleep(0.5)
            mqtt_client.loop_stop()
            mqtt_client.disconnect()
        except Exception:
            pass
        # Niet driver.quit() aanroepen: dat zou de zichtbare Chromium-sessie afsluiten.


if __name__ == "__main__":
    main()
