FROM ghcr.io/home-assistant/base:latest

ARG BUILD_VERSION
ARG BUILD_ARCH

LABEL \
    io.hass.type="app" \
    io.hass.version="${BUILD_VERSION}" \
    io.hass.arch="${BUILD_ARCH}" \
    org.opencontainers.image.title="GHL Local Bridge" \
    org.opencontainers.image.description="Local GHL to Home Assistant MQTT bridge with persistent setup browser" \
    org.opencontainers.image.source="https://github.com/D3nn1zp/ghl-local-bridge" \
    org.opencontainers.image.licenses="MIT"

RUN apk add --no-cache \
        chromium \
        chromium-chromedriver \
        python3 \
        py3-pip \
        xvfb \
        x11vnc \
        novnc \
        websockify \
        nginx \
        font-dejavu \
        xkeyboard-config \
    && pip3 install --no-cache-dir --break-system-packages \
        "selenium==4.45.0" \
        "paho-mqtt==2.1.0" \
    && rm -f /etc/nginx/http.d/default.conf \
    && mkdir -p /run/nginx

WORKDIR /app
COPY run.sh /run.sh
COPY ingress.conf /etc/nginx/http.d/ingress.conf
COPY ghl_bridge.py /app/ghl_bridge.py
RUN chmod a+x /run.sh
CMD ["/run.sh"]
