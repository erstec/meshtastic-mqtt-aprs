# meshtastic-mqtt-aprs
A Python script to translate Meshtastic MQTT packets into a plain format that other systems can easily understand. Currently takes position data and submits it to a private MQTT broker and then to private APRS-IS instance, also publishes user info packets, battery levels and environmental plugin temperatures and humidity readings to mqtt as raw values.

APRS Callsign are obtained from Short Name, dash '-' and last four hex digits of node id.

## DO NOT USE WITH aprs.fi, as it is prohibited to push non HAM data to it!

Use `meshtastic-mqtt-aprs --help` to see the options.

# Installation

Clone the repo
`git clone https://github.com/erstec/meshtastic-mqtt-aprs.git`
`cd meshtastic-mqtt-aprs`

Install to your systen with pip
`sudo apt instal python3-pip`
`pip --version`
`sudo pip install .`

Run
`meshtastic-mqtt-aprs --help` and see the options required to run the script.
Ex. `meshtastic-mqtt-aprs --mqttBroker ADDRESSOFBROKER APRSCALL APRSHOST APRSPASS`

There are some comments in meshtastic-mqtt.py that detail the tweaks needed to make this run under AppDaemon in Home Assistant.

# Running as a service
Edit service file according to your needs and copy it to systemd folder:

`sudo cp etc/systemd/system/meshtastic-mqtt-aprs.service /etc/systemd/system/meshtastic-mqtt-aprs.service`

`sudo systemctl daemon-reload`

`sudo systemctl enable meshastic-mqtt-aprs`

`sudo systemctl start meshastic-mqtt-aprs`

You can then check that your service is running by using the command:

`sudo systemctl | grep running`

`sudo systemctl status meshtastic-mqtt-aprs`

Logs:

`journalctl -f -u meshtastic-mqtt-aprs`

# Running as a Docker container
Create volume for persistent storage:
`docker volume create meshtastic-db`
Build the image:
`docker build -t meshtastic-mqtt-aprs .`
Run the container, passing all required environment variables:
docker run -d --restart unless-stopped --mount type=volume,src=meshtastic-db,target=/opt/meshtastic-mqtt-aprs --env MSH_MQTT_SERVER=<mqtt server ip/host> --env MSH_MQTT_USER=<mqtt username> --env MSH_MQTT_PSW=<mqtt password> --env MSH_APRS_PORT=<aprs-is port> --env MSH_APRS_CALL=<aprs-is callsign> --env MSH_APRS_HOST=<aprs-is host/ip> --env MSH_APRS_PASS=<aprs-is pass> meshtastic-mqtt-aprs


# Copyright notice
Based on https://github.com/joshpirihi/meshtastic-mqtt
