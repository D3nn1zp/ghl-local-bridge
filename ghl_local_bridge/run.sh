#!/usr/bin/with-contenv bashio
set -euo pipefail

bashio::log.info "GHL Local Bridge 1.0.0 starten..."

export MQTT_HOST="$(bashio::services mqtt 'host')"
export MQTT_PORT="$(bashio::services mqtt 'port')"
export MQTT_USERNAME="$(bashio::services mqtt 'username')"
export MQTT_PASSWORD="$(bashio::services mqtt 'password')"

if [[ -z "${MQTT_HOST}" ]]; then
    bashio::exit.nok "Geen MQTT-service gevonden. Installeer en start eerst Mosquitto broker."
fi

GHL_URL="$(bashio::config 'ghl_url')"
GHL_PIN="$(bashio::config 'ghl_pin')"
SETUP_UI="$(bashio::config 'setup_ui')"

export DISPLAY=:99
export CHROME_REMOTE_DEBUGGING="127.0.0.1:9222"

mkdir -p /data/chrome_profile_local /data/debug /tmp/ghl
rm -f \
    /data/chrome_profile_local/SingletonLock \
    /data/chrome_profile_local/SingletonCookie \
    /data/chrome_profile_local/SingletonSocket

PIDS=()
cleanup() {
    bashio::log.info "GHL Local Bridge stoppen..."
    for pid in "${PIDS[@]:-}"; do
        kill "${pid}" 2>/dev/null || true
    done
    wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM

Xvfb :99 -screen 0 1920x1080x24 -ac -nolisten tcp -noreset \
    >/tmp/ghl/xvfb.log 2>&1 &
PIDS+=("$!")
sleep 2

# x11vnc blijft altijd actief. Dit houdt het virtuele scherm actief, ook wanneer
# de instelbrowser is uitgeschakeld. Zonder actieve framebuffer-polling kan de
# lokale GHL-pagina achtergrondtaken en kaartupdates vertragen.
rm -f /data/vnc.pass
x11vnc \
    -display :99 \
    -forever \
    -shared \
    -nopw \
    -rfbport 5900 \
    -noxdamage \
    -repeat \
    -xkb \
    >/tmp/ghl/x11vnc.log 2>&1 &
PIDS+=("$!")

if bashio::var.true "${SETUP_UI}"; then
    websockify --web=/usr/share/novnc 6080 127.0.0.1:5900 \
        >/tmp/ghl/novnc.log 2>&1 &
    PIDS+=("$!")

    nginx -g 'daemon off;' >/tmp/ghl/nginx.log 2>&1 &
    PIDS+=("$!")

    bashio::log.info "Instelbrowser beschikbaar via Home Assistant Ingress en Open Web UI. Geen extra noVNC-wachtwoord nodig."
else
    bashio::log.info "Instelbrowser is uitgeschakeld. Chromium en het virtuele scherm blijven actief voor de bridge."
fi

CHROMIUM_BIN="$(command -v chromium-browser || command -v chromium)"

"${CHROMIUM_BIN}" \
    --no-sandbox \
    --disable-dev-shm-usage \
    --disable-gpu \
    --disable-software-rasterizer \
    --disable-notifications \
    --disable-popup-blocking \
    --disable-background-networking \
    --disable-background-timer-throttling \
    --disable-backgrounding-occluded-windows \
    --disable-renderer-backgrounding \
    --disable-features=CalculateNativeWinOcclusion \
    --disable-component-update \
    --disable-session-crashed-bubble \
    --no-first-run \
    --no-default-browser-check \
    --ignore-certificate-errors \
    --allow-running-insecure-content \
    --allow-insecure-localhost \
    --remote-debugging-address=127.0.0.1 \
    --remote-debugging-port=9222 \
    --remote-allow-origins='*' \
    --user-data-dir=/data/chrome_profile_local \
    --profile-directory=Default \
    --window-position=0,0 \
    --window-size=1920,1080 \
    --start-maximized \
    "${GHL_URL}" \
    >/tmp/ghl/chromium.log 2>&1 &
PIDS+=("$!")

bashio::log.info "Wachten tot Chromium beschikbaar is..."
python3 - <<'PYWAIT'
import time, urllib.request
for _ in range(90):
    try:
        with urllib.request.urlopen('http://127.0.0.1:9222/json/version', timeout=1) as response:
            if response.status == 200:
                raise SystemExit(0)
    except Exception:
        time.sleep(1)
raise SystemExit('Chromium remote debugging werd niet bereikbaar.')
PYWAIT

python3 /app/ghl_bridge.py &
BRIDGE_PID="$!"
PIDS+=("${BRIDGE_PID}")
wait "${BRIDGE_PID}"
