# meshtastic-mqtt-aprs
A python script to translate Meshtastic MQTT location messages into a plain format that other systems can easily understand. Currently takes position data and submits it to a private APRS-IS instance, also publishes user info packets, battery levels and environmental plugin temperatures and humidity readings to mqtt as raw values.

APRS Callsign are obtained from Short Name, dash '-' and last four hex digits of node id.

## DO NOT USE WITH aprs.fi, as it is prohibited to push non HAM data to it!

There's a few config definitions at the top of meshtastic-mqtt.py that you'll need to change for your MQTT and APRS servers.

# Installation

Clone the repo
`git clone https://github.com/erstec/meshtastic-mqtt-aprs`
`cd meshtastic-mqtt-aprs`

Edit the main script and enter your broker and/or traccar host details
`nano meshtastic_mqtt_aprs/meshtastic_mqtt_aprs.py`

Install to your systen with pip
`pip install .`

Run
`meshtastic-mqtt`

There are some comments in meshtastic-mqtt.py that detail the tweaks needed to make this run under AppDaemon in Home Assistant.

# Copyright notice
Based on https://github.com/joshpirihi/meshtastic-mqtt
