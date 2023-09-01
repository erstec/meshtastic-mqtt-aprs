# python3.6

import meshtastic_mqtt_aprs.portnums_pb2 as portnums_pb2
from meshtastic_mqtt_aprs.portnums_pb2 import ENVIRONMENTAL_MEASUREMENT_APP, POSITION_APP

import random
import json

import argparse

import aprslib
from datetime import datetime

import meshtastic_mqtt_aprs.mesh_pb2 as mesh_pb2
import meshtastic_mqtt_aprs.mqtt_pb2 as mqtt_pb2
import meshtastic_mqtt_aprs.environmental_measurement_pb2 as environmental_measurement_pb2

from paho.mqtt import client as mqtt_client

from paho.mqtt import client as mqtt_client
from google.protobuf.json_format import MessageToJson

import telebot

#uncomment for AppDaemon
#import hassapi as hass

#swap for AppDaemon
#class MeshtasticMQTT(hass.Hass=None):
class MeshtasticMQTT():
    print ("Meshtastic MQTT APRS 2.1.5")

    parser = argparse.ArgumentParser(description='Meshtastic MQTT APRS', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--mqttServer', default='localhost', help='MQTT Broker Address')
    parser.add_argument('--mqttPort', default=1883, type=int, help='MQTT Broker Port')
    parser.add_argument('--mqttUsername', default='', help='MQTT Broker Username')
    parser.add_argument('--mqttPassword', default='', help='MQTT Broker Password')

    parser.add_argument('aprscall', help='APRS Call')
    parser.add_argument('aprsHost', help='APRS Host')
    #parser.add_argument('--aprsPort', default='14580', type=int, help='APRS Port')
    parser.add_argument('--aprsPort', default='14580', help='APRS Port')
    parser.add_argument('aprsPass', help='APRS Passcode')
    parser.add_argument('--aprsTable', default='/', help='APRS Table')
    parser.add_argument('--aprsSymbol', default='`', help='APRS Symbol')

    parser.add_argument('--telegramToken', default='', help='Telegram Token')
    parser.add_argument('--telegramChatId', default='', help='Telegram Chat ID')

    args = parser.parse_args()
    config = vars(args)
    print(config)

    broker = config['mqttServer']
    username = config['mqttUsername']
    password = config['mqttPassword']
    port = config['mqttPort']
    # topic = "msh/2/c/#"
    # topic = "msh/2/json/#"
    # QoS = 0 - At most once (default) - best effort delivery
    # QoS = 1 - At least once - guaranteed delivery
    # QoS = 2 - Exactly once - assured delivery
    topics = [("msh/2/json/#", 1), ("msh/2/c/#", 0)]
    # generate client ID with pub prefix randomly
    client_id = f'meshtastic-mqtt-{random.randint(0, 100)}'
    
    prefix = "meshtastic/"

    aprsCall = config['aprscall']
    aprsHost = config['aprsHost']
    aprsPort = config['aprsPort']
    aprsPass = config['aprsPass']
    aprsTable = config['aprsTable']
    aprsSymbol = config['aprsSymbol']

    telegramToken = config['telegramToken']
    telegramChatId = config['telegramChatId']

    # APRS Telemetry
    # Values: voltage, current, temperature, relative_humidity, barometric_pressure
    aprsTlmNames = "Volt,Curr,Temp,Hum,Press"
    aprsTlmUnits = "Volt,Amp,deg.C,Perc,hPa"
    aprsTlmEqns = "0,1,0,0,1,0,0,1,0,0,1,0,0,1,0"
    # a·x2 + b·x + c

    # Id -> Callsign DB
    calldict = {
    }

    current_data = {
    }

    # Telegram Bot
    bot = telebot.TeleBot(telegramToken)
    
    print("Loading CallDB...")
    try:
        with open('calldb.json') as json_file:
            calldict = json.load(json_file)
    except:
        print("calldb.json not found")
    print(calldict)

    print("Loading CurrentData...")
    for key in calldict:
        current_data[key] = {
            "latitude_i": 0,
            "longitude_i": 0,
            "altitude": 0,
            "battery_level": 0,
            "voltage": 0,
            "barometric_pressure": 0,
            "current": 0,
            "gas_resistance": 0,
            "relative_humidity": 0,
            "temperature": 0,
            "channel_utilization": 0,
            "air_util_tx": 0,
            "rssi": "",
            "snr": "",
            "hardware": "",
            "aprsTlmCnt": 0,
            "aprsAnnounceSent": False,
            "lastMsgId": 0,
            "lastMsgIdOld": 0,
        }
    print(current_data)
    
    from pathlib import Path
    print(f"Running dir: `{Path.cwd()}`")

    def connect_mqtt(self) -> mqtt_client:
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                print("(RUN) Connected to MQTT Broker!")
            else:
                print("(RUN) Failed to connect, return code %d\n", rc)

        client = mqtt_client.Client(self.client_id)
        client.username_pw_set(self.username, self.password)
        client.on_connect = on_connect
        client.connect(self.broker, self.port)
        return client


    def subscribe(self, client: mqtt_client):
        def on_message(client, userdata, msg):
            #print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic") // obsolete
            # print(f"Received `{msg.payload}` from `{msg.topic}` topic")
            print("------------------")
            print(f"Received msg from `{msg.topic}` topic")

            topic_mode = msg.topic.split("/")[3]
            print(f"Topic mode: {topic_mode}")

            is_it_json = False
            it_is_old = False

            # Try Parse
            try:
                se = mqtt_pb2.ServiceEnvelope()
                se.ParseFromString(msg.payload)
                mp = se.packet
                # print(f"Received2o: `{se}`")
                # print(f"Received2o / '{mp}'")
                print(f"Received2o / '{mp.decoded.portnum}'")
                
                if getattr(mp, "from") == 4:
                    print("ID = 4 detected! Aborting!")
                    return

                # Check if message is already received before
                if str(getattr(mp, "from")) in self.current_data:
                    if "lastMsgIdOld" in self.current_data[str(getattr(mp, "from"))]:
                        if self.current_data[str(getattr(mp, "from"))]["lastMsgIdOld"] == mp.id:
                            print("Message already received")
                            return

                it_is_old = True
            except:
                try:
                    json_unpacked = json.loads(msg.payload)
                    print(f"Received2n: `{json_unpacked}`")

                    payload = json_unpacked["payload"]
                    # print(payload)

                    from_node = str(json_unpacked["from"])
                    to_node = str(json_unpacked["to"])

                    msg_id = str(json_unpacked["id"])

                    if json_unpacked["from"] == 4:
                        print("ID = 4 detected! Aborting!")
                        return

                    # Check if message is already received before
                    if from_node in self.current_data:
                        if "lastMsgId" in self.current_data[from_node]:
                            if self.current_data[from_node]["lastMsgId"] == msg_id:
                                print("Message already received")
                                return

                    is_it_json = True
                except:
                    print("Received2x: `Failed to parse`")

            if it_is_old:
                if mp.decoded.portnum == portnums_pb2.POSITION_APP:
                    print("OLD Position/Signal Quality received")
                    snr = str(mp.rx_snr)
                    print("SNR: " + snr)
                    if str(getattr(mp, "from")) in self.current_data:
                        if mp.rx_snr == 0:
                            if self.current_data[str(getattr(mp, "from"))]["snr"] != "":
                                snr = self.current_data[str(getattr(mp, "from"))]["snr"]
                        else:
                            self.current_data[str(getattr(mp, "from"))]["snr"] = snr

                    rssi = str(mp.priority)
                    print("RSSI: " + rssi)
                    if str(getattr(mp, "from")) in self.current_data:
                        if mp.priority == 0:
                            if self.current_data[str(getattr(mp, "from"))]["rssi"] != "":
                                rssi = self.current_data[str(getattr(mp, "from"))]["rssi"]
                        else:
                            self.current_data[str(getattr(mp, "from"))]["rssi"] = rssi
                    
                    print("RSSI: " + rssi + " SNR: " + snr)
                    
                    link_quality = {
                        "rssi": rssi,
                        "snr": snr
                    }
                    client.publish(self.prefix + str(getattr(mp, "from")) + "/link_quality", json.dumps(link_quality))

                    # Save message id to prevent duplicate messages from being processed
                    if str(getattr(mp, "from")) in self.current_data:
                        self.current_data[str(getattr(mp, "from"))]["lastMsgIdOld"] = mp.id

            elif is_it_json:
                if json_unpacked["type"] == "position":
                    print("Position received")
                    owntracks_payload = {
                        "_type": "location",
                        "lat": payload["latitude_i"] * 1e-7,
                        "lon": payload["longitude_i"] * 1e-7,
                    }
                    if "altitude" in payload:
                        owntracks_payload["alt"] = payload["altitude"]
                    if "time" in payload:
                        owntracks_payload["tst"] = payload["time"]

                    if owntracks_payload["lat"] != 0 and owntracks_payload["lon"] != 0:
                        #client.publish("owntracks/"+str(getattr(mp, "from"))+"/meshtastic_node", json.dumps(owntracks_payload))
                        client.publish(self.prefix + from_node + "/position", json.dumps(owntracks_payload))
                        
                        #deal with APRS
                        print(self.calldict)
                        if from_node in self.calldict:
                            print("(CALL DB) Call is in DB, uploading to APRS")
                            if len(self.aprsHost) > 0 and len(self.aprsPort) > 0 and len(self.aprsHost) > 0:
                                print('----- APRS sending -----')
                                try:
                                    AIS = aprslib.IS(self.aprsCall, passwd=self.aprsPass, host=self.aprsHost, port=self.aprsPort)
                                    AIS.connect()
                                except:
                                    print("An exception occurred")
                                    return

                                DestCallsign = self.calldict[from_node][0] # take short name
                                DestCallsign = DestCallsign + "-"
                                DestCallsign = DestCallsign + format(json_unpacked["from"] & (2**32-1), 'x')[-4:] #last 4 bytes of ID
                                DestCallsignUnaligned = DestCallsign
                                DestCallsign = DestCallsign.ljust(9, ' ')
                                
                                # if "tst" in owntracks_payload:
                                    #  now = owntracks_payload["tst"]
                                # else:
                                    # now = datetime.utcnow()

                                now = datetime.utcnow()
                                TimeStamp = now.strftime("%d%H%M")
                                
                                deg = owntracks_payload["lat"]
                                # print(deg)
                                
                                dd1 = abs(float(deg))
                                cdeg = int(dd1)
                                cmin = int((dd1 - cdeg) * 60)
                                csec = ((dd1 - cdeg) * 60 - cmin) * 100
                                if deg < 0: cdeg = cdeg * -1
                                
                                Latitude = "%02d%02d.%02d" % (cdeg, cmin, csec)
                                # print(Latitude)
                                if deg > 0:
                                    LatitudeNS = 'N'
                                else:
                                    LatitudeNS = 'S'

                                deg = owntracks_payload["lon"]
                                # print(deg)
                                
                                dd1 = abs(float(deg))
                                cdeg = int(dd1)
                                cmin = int((dd1 - cdeg) * 60)
                                csec = ((dd1 - cdeg) * 60 - cmin) * 100
                                if deg < 0: cdeg = cdeg * -1
                                
                                Longitude = "%03d%02d.%02d" % (cdeg, cmin, csec)
                                # print(Longitude)
                                if deg > 0:
                                    LongitudeEW = 'E'
                                else:
                                    LongitudeEW = "W"

                                Comment = 'MeshTastic'
                                if topic_mode == "MediumFast" or topic_mode == "LongFast":
                                    Comment = Comment + ' ' + topic_mode
                                if self.current_data[from_node]["hardware"] != "":
                                    Comment = Comment + ' ' + str(self.current_data[from_node]["hardware"])
                                Comment = Comment + ' ' + self.calldict[from_node][1]
                                if self.current_data[from_node]["rssi"] != "":
                                    Comment = Comment + ' RSSI: ' + str(self.current_data[from_node]["rssi"]) + ' dBm'
                                if self.current_data[from_node]["snr"] != "":
                                    Comment = Comment + ' SNR: ' + str(self.current_data[from_node]["snr"]) + ' dB'
                                if "alt" in owntracks_payload:
                                    Comment = Comment + ' Alt: ' + str(owntracks_payload["alt"]) + 'm'
                                else:                                    
                                    if self.current_data[from_node]["altitude"] != 0:
                                        Comment = Comment + ' Alt: ' + f'{self.current_data[from_node]["altitude"]:.1f}' + 'm'
                                if self.current_data[from_node]["temperature"] != 0:
                                    Comment = Comment + ' ' + f'{self.current_data[from_node]["temperature"]:.1f}' + 'C'
                                if self.current_data[from_node]["relative_humidity"] != 0:
                                    Comment = Comment + ' RH: ' + f'{self.current_data[from_node]["relative_humidity"]:.1f}' + '%'
                                if self.current_data[from_node]["barometric_pressure"] != 0:
                                    Comment = Comment + ' ' + f'{self.current_data[from_node]["barometric_pressure"]:.1f}' + 'hPa'
                                if self.current_data[from_node]["gas_resistance"] != 0:
                                    Comment = Comment + ' GasR: ' + f'{self.current_data[from_node]["gas_resistance"]:.1f}' + 'Ohm'
                                #if self.current_data[from_node]["battery_level"] != 0:
                                Comment = Comment + ' Bat: ' + f'{self.current_data[from_node]["battery_level"]:.0f}' + '%'
                                #if self.current_data[from_node]["voltage"] != 0:
                                Comment = Comment + ' ' + f'{self.current_data[from_node]["voltage"]:.2f}' + 'V'
                                if self.current_data[from_node]["current"] != 0:
                                    Comment = Comment + ' ' + f'{self.current_data[from_node]["current"]:.1f}' + 'A'
                                if self.current_data[from_node]["channel_utilization"] != 0:
                                    Comment = Comment + ' ChUtil: ' + f'{self.current_data[from_node]["channel_utilization"]:.1f}' + '%'
                                if self.current_data[from_node]["air_util_tx"] != 0:
                                    Comment = Comment + ' AirUtil: ' + f'{self.current_data[from_node]["air_util_tx"]:.1f}' + '%'

                                # Comment field in Position report Max. 43 chars // http://www.aprs.org/doc/APRS101.PDF
                                # But we see it is not truncated by APRS-IS, so use as much as we need
                                # comment_length = len(Comment)
                                # print(f"Comment length: {comment_length}")
                                # if comment_length > 43:
                                #     print(f"Comment too long: {comment_length - 43}")
                                #     Comment = Comment[:43]
                                #     print(f"Truncating Comment to: {Comment}")

                                # MESSAGEpacket = f'{self.aprsCall}>APZ32E,WIDE1-1:={Latitude}{LatitudeNS}\{Longitude}{LongitudeEW}S{Comment}\n'
                                # MESSAGEpacket = f'{self.aprsCall}>APZ32E,WIDE1-1:;{DestCallsign}*{TimeStamp}z{Latitude}{LatitudeNS}{self.aprsTable}{Longitude}{LongitudeEW}{self.aprsSymbol}{Comment}\n'
                                if topic_mode == "LongFast":
                                    aprs_symbol = "r"
                                else:
                                    aprs_symbol = self.aprsSymbol
                                MESSAGEpacket = f'{DestCallsignUnaligned}>APZ32E,WIDE1-1:;{DestCallsign}*{TimeStamp}z{Latitude}{LatitudeNS}{self.aprsTable}{Longitude}{LongitudeEW}{aprs_symbol}{Comment}\n'
                                print('Sending APRS message')
                                print(MESSAGEpacket)

                                self.current_data[from_node]["lat"] = owntracks_payload["lat"]
                                self.current_data[from_node]["lon"] = owntracks_payload["lon"]
                                if "alt" in owntracks_payload:
                                    if owntracks_payload["alt"] != 0:
                                        self.current_data[from_node]["alt"] = owntracks_payload["alt"]

                                try:
                                    AIS.sendall(MESSAGEpacket)
                                    AIS.close()
                                except:
                                    print("APRS SEND: Exception occurred")

                                # Save message ID to DB to avoid duplicate messages parsing
                                if from_node in self.current_data:
                                    self.current_data[from_node]["lastMsgId"] = msg_id
                        else:
                            print("(CALL DB) Call is NOT in DB, skip APRS upload")
                
                elif json_unpacked["type"] == "telemetry":                
                    print("Telemetry received")

                    if "voltage" in payload:
                        if payload["voltage"] != None:
                            if payload["voltage"] > 0:
                                client.publish(self.prefix + from_node + "/voltage", payload["voltage"])
                                if from_node in self.current_data:
                                    self.current_data[from_node]["voltage"] = payload["voltage"]
                    
                    if "air_util_tx" in payload:
                        if payload["air_util_tx"] != None:
                            if payload["air_util_tx"] > 0:
                                client.publish(self.prefix + from_node + "/air_util_tx", payload["air_util_tx"])
                                if from_node in self.current_data:
                                    self.current_data[from_node]["air_util_tx"] = payload["air_util_tx"]

                    if "channel_utilization" in payload:
                        if payload["channel_utilization"] != None:
                            if payload["channel_utilization"] > 0:
                                client.publish(self.prefix + from_node + "/channel_utilization", payload["channel_utilization"])
                                if from_node in self.current_data:
                                    self.current_data[from_node]["channel_utilization"] = payload["channel_utilization"]
                    
                    if "battery_level" in payload:
                        if payload["battery_level"] != None:
                            if payload["battery_level"] > 0:
                                client.publish(self.prefix + from_node + "/battery_level", payload["battery_level"])
                                if from_node in self.current_data:
                                    self.current_data[from_node]["battery_level"] = payload["battery_level"]
                    
                    if "barometric_pressure" in payload:
                        if payload["barometric_pressure"] != None:
                            if payload["barometric_pressure"] > 0:
                                client.publish(self.prefix + from_node + "/barometric_pressure", payload["barometric_pressure"])
                                if from_node in self.current_data:
                                    self.current_data[from_node]["barometric_pressure"] = payload["barometric_pressure"]

                    if "temperature" in payload:
                        if payload["temperature"] != None:
                            if payload["temperature"] > 0:
                                client.publish(self.prefix + from_node + "/temperature", payload["temperature"])
                                if from_node in self.current_data:
                                    self.current_data[from_node]["temperature"] = payload["temperature"]

                    if "relative_humidity" in payload:
                        if payload["relative_humidity"] != None:
                            if payload["relative_humidity"] > 0:
                                client.publish(self.prefix + from_node + "/relative_humidity", payload["relative_humidity"])
                                if from_node in self.current_data:
                                    self.current_data[from_node]["relative_humidity"] = payload["relative_humidity"]

                    if "gas_resistance" in payload:
                        if payload["gas_resistance"] != None:
                            if payload["gas_resistance"] > 0:
                                client.publish(self.prefix + from_node + "/gas_resistance", payload["gas_resistance"])
                                if from_node in self.current_data:
                                    self.current_data[from_node]["gas_resistance"] = payload["gas_resistance"]
                    
                    if "current" in payload:
                        if payload["current"] != None:
                            if payload["current"] > 0:
                                client.publish(self.prefix + from_node + "/current", payload["current"])
                                if from_node in self.current_data:
                                    self.current_data[from_node]["current"] = payload["current"]
                    
                    print('----- APRS sending -----')
                    try:
                        AIS = aprslib.IS(self.aprsCall, passwd=self.aprsPass, host=self.aprsHost, port=self.aprsPort)
                        AIS.connect()
                    except:
                        print("An exception occurred")
                        return

                    if from_node in self.calldict:   
                        DestCallsign = self.calldict[from_node][0] # take short name
                        DestCallsign = DestCallsign + "-"
                        DestCallsign = DestCallsign + format(json_unpacked["from"] & (2**32-1), 'x')[-4:] #last 4 bytes of ID
                        DestCallsignUnaligned = DestCallsign
                        DestCallsign = DestCallsign.ljust(9, ' ')

                        if self.current_data[from_node]["aprsTlmCnt"] % 6 == 0:
                            print("Sending APRS Telemetry Announce")
                            MESSAGEpacketAll = f'{DestCallsignUnaligned}>APZ32E::{DestCallsign}:PARM.{self.aprsTlmNames}\r\n'
                            MESSAGEpacketAll = MESSAGEpacketAll + f'{DestCallsignUnaligned}>APZ32E::{DestCallsign}:UNIT.{self.aprsTlmUnits}\r\n'
                            MESSAGEpacketAll = MESSAGEpacketAll + f'{DestCallsignUnaligned}>APZ32E::{DestCallsign}:EQNS.{self.aprsTlmEqns}\r\n'

                            print(MESSAGEpacketAll)
                            
                            try:
                                AIS.sendall(MESSAGEpacketAll)
                                self.current_data[from_node]["aprsAnnounceSent"] = True
                            except:
                                print("APRS SEND: Exception occurred")
                            
                        if self.current_data[from_node]["aprsAnnounceSent"] == True:
                            # Values: voltage, current, temperature, relative_humidity, barometric_pressure
                            #val1 = "{:0}".format(self.current_data[from_node]["voltage"] * 100)
                            #val1 = round(self.current_data[from_node]["voltage"] * 100, 0)
                            val1 = int(self.current_data[from_node]["voltage"] * 10)
                            val2 = int(self.current_data[from_node]["current"] * 10)
                            val3 = int(self.current_data[from_node]["temperature"] * 10)
                            val4 = int(self.current_data[from_node]["relative_humidity"])
                            val5 = int(self.current_data[from_node]["barometric_pressure"])
                            # MESSAGEpacketTLM = f'{self.aprsCall}:T#{self.current_data[from_node]["aprsTlmCnt"]:03d},{self.current_data[from_node]["voltage"]:.2f},{self.current_data[from_node]["current"]:.1f},{self.current_data[from_node]["temperature"]:.1f},{self.current_data[from_node]["relative_humidity"]:.0f},{self.current_data[from_node]["barometric_pressure"]:.0f},00000000\n'
                            MESSAGEpacketTLM = f'{DestCallsignUnaligned}>APZ32E:T#{self.current_data[from_node]["aprsTlmCnt"]:03d},{val1},{val2},{val3},{val4},{val5},00000000\r\n'
                            print('Sending APRS Telemetry Packet')
                            print(MESSAGEpacketTLM)

                            try:
                                AIS.sendall(MESSAGEpacketTLM)
                            except:
                                print("APRS SEND: Exception occurred")

                            # Telemetry packet counter [000-999]
                            self.current_data[from_node]["aprsTlmCnt"] += 1
                            if self.current_data[from_node]["aprsTlmCnt"] > 999:
                                self.current_data[from_node]["aprsTlmCnt"] = 0
                        
                        else:
                            print('NOT Sending APRS Telemetry Packet, APRS announce not sent yet')
                        
                        # Save message ID to DB to avoid duplicate messages parsing
                        if from_node in self.current_data:
                            self.current_data[from_node]["lastMsgId"] = msg_id
                            
                        try:
                            AIS.close()
                        except:
                            print("APRS SEND: Exception occurred")
                    else:
                        print("(CALL DB) Call is NOT in DB, skip APRS Telemetry upload")

                elif json_unpacked["type"] == "nodeinfo":
                    print("Nodeinfo received")

                    client.publish(self.prefix + from_node + "/user", json.dumps(payload))

                    if not from_node in self.current_data:
                        self.current_data[from_node] = {
                            "latitude_i": 0,
                            "longitude_i": 0,
                            "altitude": 0,
                            "battery_level": 0,
                            "voltage": 0,
                            "barometric_pressure": 0,
                            "current": 0,
                            "gas_resistance": 0,
                            "relative_humidity": 0,
                            "temperature": 0,
                            "channel_utilization": 0,
                            "air_util_tx": 0,
                            "rssi": "",
                            "snr": "",
                            "hardware": "",
                            "aprsTlmCnt": 0,
                            "aprsAnnounceSent": False,
                            "lastMsgId": 0,
                            "lastMsgIdOld": 0,
                        }
                    
                    if "hardware" in payload:
                        # self.current_data[from_node]["hardware"] = payload["hardware"]
                        if payload["hardware"] == 0:
                            self.current_data[from_node]["hardware"] = "UNSET"
                        elif payload["hardware"] == 1:
                            self.current_data[from_node]["hardware"] = "TLORA_V2"
                        elif payload["hardware"] == 2:
                            self.current_data[from_node]["hardware"] = "TLORA_V1"
                        elif payload["hardware"] == 3:
                            self.current_data[from_node]["hardware"] = "TLORA_V2_1_1P6"
                        elif payload["hardware"] == 4:
                            self.current_data[from_node]["hardware"] = "TBEAM"
                        elif payload["hardware"] == 5:
                            self.current_data[from_node]["hardware"] = "HELTEC_V2_0"
                        elif payload["hardware"] == 6:
                            self.current_data[from_node]["hardware"] = "TBEAM_V0P7"
                        elif payload["hardware"] == 7:
                            self.current_data[from_node]["hardware"] = "T_ECHO"
                        elif payload["hardware"] == 8:
                            self.current_data[from_node]["hardware"] = "TLORA_V1_1P3"
                        elif payload["hardware"] == 9:
                            self.current_data[from_node]["hardware"] = "RAK4631"
                        elif payload["hardware"] == 10:
                            self.current_data[from_node]["hardware"] = "HELTEC_V2_1"
                        elif payload["hardware"] == 11:
                            self.current_data[from_node]["hardware"] = "HELTEC_V1"
                        elif payload["hardware"] == 12:
                            self.current_data[from_node]["hardware"] = "LILYGO_TBEAM_S3_CORE"
                        elif payload["hardware"] == 13:
                            self.current_data[from_node]["hardware"] = "RAK11200"
                        elif payload["hardware"] == 14:
                            self.current_data[from_node]["hardware"] = "NANO_G1"
                        elif payload["hardware"] == 15:
                            self.current_data[from_node]["hardware"] = "TLORA_V2_1_1P8"
                        elif payload["hardware"] == 16:
                            self.current_data[from_node]["hardware"] = "TLORA_T3_S3"
                        elif payload["hardware"] == 17:
                            self.current_data[from_node]["hardware"] = "NANO_G1_EXPLORER"
                        elif payload["hardware"] == 25:
                            self.current_data[from_node]["hardware"] = "STATION_G1"
                        elif payload["hardware"] == 26:
                            self.current_data[from_node]["hardware"] = "RAK11310"
                        elif payload["hardware"] == 32:
                            self.current_data[from_node]["hardware"] = "LORA_RELAY_V1"
                        elif payload["hardware"] == 33:
                            self.current_data[from_node]["hardware"] = "NRF52840DK"
                        elif payload["hardware"] == 34:
                            self.current_data[from_node]["hardware"] = "PPR"
                        elif payload["hardware"] == 35:
                            self.current_data[from_node]["hardware"] = "GENIEBLOCKS"
                        elif payload["hardware"] == 36:
                            self.current_data[from_node]["hardware"] = "NRF52_UNKNOWN"
                        elif payload["hardware"] == 37:
                            self.current_data[from_node]["hardware"] = "PORTDUINO"
                        elif payload["hardware"] == 38:
                            self.current_data[from_node]["hardware"] = "ANDROID_SIM"
                        elif payload["hardware"] == 39:
                            self.current_data[from_node]["hardware"] = "DIY_V1"
                        elif payload["hardware"] == 40:
                            self.current_data[from_node]["hardware"] = "NRF52840_PCA10059"
                        elif payload["hardware"] == 41:
                            self.current_data[from_node]["hardware"] = "DR_DEV"
                        elif payload["hardware"] == 42:
                            self.current_data[from_node]["hardware"] = "M5STACK"
                        elif payload["hardware"] == 43:
                            self.current_data[from_node]["hardware"] = "HELTEC_V3"
                        elif payload["hardware"] == 44:
                            self.current_data[from_node]["hardware"] = "HELTEC_WSL_V3"
                        elif payload["hardware"] == 45:
                            self.current_data[from_node]["hardware"] = "BETAFPV_2400_TX"
                        elif payload["hardware"] == 46:
                            self.current_data[from_node]["hardware"] = "BETAFPV_900_NANO_TX"
                        elif payload["hardware"] == 47:
                            self.current_data[from_node]["hardware"] = "RPI_PICO"
                        elif payload["hardware"] == 255:
                            self.current_data[from_node]["hardware"] = "PRIVATE_HW"
                        else:
                            self.current_data[from_node]["hardware"] = "UNKNOWN"

                    print('------------------ CALL DB STR ------------------')
                    data_list = [payload["shortname"], payload["longname"]]
                    self.calldict[from_node] = data_list
                    print(self.calldict)
                    #json_object = json.dumps(self.calldict, indent = 4)
                    #print(json_object)
                    with open("calldb.json", "w") as outfile:
                        json.dump(self.calldict, outfile)
                    print('------------------ CALL DB END ------------------')

                    # Save message ID to DB to avoid duplicate messages parsing
                    if from_node in self.current_data:
                        self.current_data[from_node]["lastMsgId"] = msg_id

                elif json_unpacked["type"] == "text":
                    print("Text received")
                    text = {
                        "message": payload["text"],
                        "from": from_node,
                        "to": to_node
                    }
                    client.publish(self.prefix + from_node + "/text_message", json.dumps(text))

                    self.bot.send_message(self.telegramChatId, f"Message from {from_node}: {payload['text']}")

                    # Save message ID to DB to avoid duplicate messages parsing
                    if from_node in self.current_data:
                        self.current_data[from_node]["lastMsgId"] = msg_id

        client.subscribe(self.topics)
        client.on_message = on_message


    def run(self): #on appdaemon remove the argument here
        client = self.connect_mqtt()
        self.subscribe(client)
        client.loop_forever()

    def initialize(self):
        self.run(self)

def main():
    mm = MeshtasticMQTT()
    mm.run()


#in appdaemon comment this block out
if __name__ == '__main__':
    main()
