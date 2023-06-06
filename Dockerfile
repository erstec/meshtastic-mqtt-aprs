#
# Meshtastic 2.0 to APRS-IS gateway
# Please use your own aprs-is server and don't upstream it to public servers
# You can use it i.e. with your own APRS Track Direct implementation
#

FROM python:3.9-alpine


WORKDIR /opt/meshtastic-mqtt-aprs

RUN apk add --no-cache git \
 && git clone -b main https://github.com/erstec/meshtastic-mqtt-aprs.git . \
 && pip3 install . \
 && cd /tmp && rm -rf /opt/meshtastic-mqtt-aprs \
 && apk del git

# meshtastic install files can be removed after installation

WORKDIR /tmp

LABEL description="MeshTastic 2.0 MQTT to APRS gateway"
ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["/usr/local/bin/python3","/usr/local/bin/meshtastic-mqtt-aprs"]
