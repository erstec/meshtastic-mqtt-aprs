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

#uncomment for AppDaemon
#import hassapi as hass

#swap for AppDaemon
#class MeshtasticMQTT(hass.Hass=None):
class MeshtasticMQTT():
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

    args = parser.parse_args()
    config = vars(args)
    print(config)

    broker = config['mqttServer']
    username = config['mqttUsername']
    password = config['mqttPassword']
    port = config['mqttPort']
    topic = "msh/2/c/#"
    # generate client ID with pub prefix randomly
    client_id = f'meshtastic-mqtt-{random.randint(0, 100)}'
    
    prefix = "meshtastic/"

    aprsCall = config['aprscall']
    aprsHost = config['aprsHost']
    aprsPort = config['aprsPort']
    aprsPass = config['aprsPass']
    aprsTable = config['aprsTable']
    aprsSymbol = config['aprsSymbol']

    # Id -> Callsign DB
    calldict = {
    }

    current_data = {
    }
    
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
            "shortName": calldict[key][0],
            "longName": calldict[key][1],
            "lat": 0,
            "lon": 0,
            "alt": 0,
            "batteryVoltage": 0,
            "temperature": 0,
            "humidity": 0,
            "pressure": 0,
            "lastPacketRSSI": 0,
            "lastPacketSNR": 0,
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
            se = mqtt_pb2.ServiceEnvelope()
            se.ParseFromString(msg.payload)

            print(f"Received2: `{se}`")
            mp = se.packet

            if mp.decoded.portnum == portnums_pb2.POSITION_APP:
                pos = mesh_pb2.Position()
                pos.ParseFromString(mp.decoded.payload)
                print(getattr(mp, "from"))
                print(f"->'{pos}'")
                owntracks_payload = {
                    "_type": "location",
                    "lat": pos.latitude_i * 1e-7,
                    "lon": pos.longitude_i * 1e-7,
                    "tst": pos.time,
                    "batt": pos.battery_level,
                    "alt": pos.altitude
                }
                if owntracks_payload["lat"] != 0 and owntracks_payload["lon"] != 0:
                    #client.publish("owntracks/"+str(getattr(mp, "from"))+"/meshtastic_node", json.dumps(owntracks_payload))
                    client.publish(self.prefix+str(getattr(mp, "from"))+"/position", json.dumps(owntracks_payload))
                    #deal with APRS
                    print(self.calldict)
                    if str(getattr(mp, "from")) in self.calldict:
                        print("(CALL DB) Call is in DB, uploading to APRS")
                        if len(self.aprsHost) > 0 and len(self.aprsPort) > 0 and len(self.aprsHost) > 0:
                            print('------------------------ APRS sending... ------------------------ ')
                            try:
                                AIS = aprslib.IS(self.aprsCall, passwd=self.aprsPass, host=self.aprsHost, port=self.aprsPort)
                                AIS.connect()
                            except:
                                print("An exception occurred")

                            DestCallsign = self.calldict[str(getattr(mp, "from"))][0] # take short name
                            DestCallsign = DestCallsign + "-"
                            DestCallsign = DestCallsign + format(getattr(mp, "from") & (2**32-1), 'x')[-4:] #last 4 bytes of ID
                            DestCallsign = DestCallsign.ljust(9, ' ')
                            
                            now = datetime.utcnow()
                            TimeStamp = now.strftime("%d%H%M")
                            
                            deg = owntracks_payload["lat"]
                            print(deg)
                            
                            dd1 = abs(float(deg))
                            cdeg = int(dd1)
                            cmin = int((dd1 - cdeg) * 60)
                            csec = ((dd1 - cdeg) * 60 - cmin) * 100
                            if deg < 0: cdeg = cdeg * -1
                            
                            Latitude = "%02d%02d.%02d" % (cdeg, cmin, csec)
                            print(Latitude)
                            if deg > 0:
                                LatitudeNS = 'N'
                            else:
                                LatitudeNS = 'S'

                            deg = owntracks_payload["lon"]
                            print(deg)
                            
                            dd1 = abs(float(deg))
                            cdeg = int(dd1)
                            cmin = int((dd1 - cdeg) * 60)
                            csec = ((dd1 - cdeg) * 60 - cmin) * 100
                            if deg < 0: cdeg = cdeg * -1
                            
                            Longitude = "%03d%02d.%02d" % (cdeg, cmin, csec)
                            print(Longitude)
                            if deg > 0:
                                LongitudeEW = 'E'
                            else:
                                LongitudeEW = "W"

                            snr = str(mp.rx_snr)
                            if mp.rx_snr == 0:
                                if self.current_data[str(getattr(mp, "from"))]["lastPacketSNR"] != 0:
                                    snr = str(self.current_data[str(getattr(mp, "from"))]["lastPacketSNR"])
                                else:
                                    snr = 'n/a'
                            rssi = str(mp.priority)
                            if mp.priority == 0:
                                if self.current_data[str(getattr(mp, "from"))]["lastPacketRSSI"] != 0:
                                    rssi = str(self.current_data[str(getattr(mp, "from"))]["lastPacketRSSI"])
                                else:
                                    rssi = 'n/a'
                            Comment = 'MeshTastic ' + self.calldict[str(getattr(mp, "from"))][1] + ' SNR: ' + snr + ' dB RSSI: ' + rssi + ' dBm' # add long name from DB
                            if self.current_data[str(getattr(mp, "from"))]["alt"] != 0:
                                Comment = Comment + ' ' + f'{self.current_data[str(getattr(mp, "from"))]["alt"]:.1f}' + 'm'
                            if self.current_data[str(getattr(mp, "from"))]["batteryVoltage"] != 0:
                                Comment = Comment + ' ' + f'{self.current_data[str(getattr(mp, "from"))]["batteryVoltage"]:.2f}' + 'V'
                            if self.current_data[str(getattr(mp, "from"))]["temperature"] != 0:
                                Comment = Comment + ' ' + f'{self.current_data[str(getattr(mp, "from"))]["temperature"] / 1e22:.1f}' + 'C'
                            if self.current_data[str(getattr(mp, "from"))]["humidity"] != 0:
                                Comment = Comment + ' ' + f'{self.current_data[str(getattr(mp, "from"))]["humidity"]:.1f}' + '%'
                            if self.current_data[str(getattr(mp, "from"))]["pressure"] != 0:
                                Comment = Comment + ' ' + f'{self.current_data[str(getattr(mp, "from"))]["pressure"]:.2f}' + 'hPa'

                            # MESSAGEpacket = f'{self.aprsCall}>APZ32E,WIDE1-1:={Latitude}{LatitudeNS}\{Longitude}{LongitudeEW}S{Comment}\n'
                            MESSAGEpacket = f'{self.aprsCall}>APZ32E,WIDE1-1:;{DestCallsign}*{TimeStamp}z{Latitude}{LatitudeNS}{self.aprsTable}{Longitude}{LongitudeEW}{self.aprsSymbol}{Comment}\n'
                            print('Sending message')
                            print(MESSAGEpacket)

                            self.current_data[str(getattr(mp, "from"))]["lat"] = owntracks_payload["lat"]
                            self.current_data[str(getattr(mp, "from"))]["lon"] = owntracks_payload["lon"]
                            if owntracks_payload["alt"] != 0:
                                self.current_data[str(getattr(mp, "from"))]["alt"] = owntracks_payload["alt"]
                            if snr != 'n/a':
                                self.current_data[str(getattr(mp, "from"))]["lastPacketSNR"] = snr
                            if rssi != 'n/a':
                                self.current_data[str(getattr(mp, "from"))]["lastPacketRSSI"] = rssi

                            try:
                                AIS.sendall(MESSAGEpacket)
                                AIS.close()
                            except:
                                print("APRS SEND: Exception occurred")
                    else:
                        print("(CALL DB) Call is NOT in DB, skip APRS upload")
                #lets also publish the battery directly
                if pos.battery_level > 0:
                    client.publish(self.prefix+str(getattr(mp, "from"))+"/battery", pos.battery_level)
                    if str(getattr(mp, "from")) in self.current_data:
                        self.current_data[str(getattr(mp, "from"))]["batteryVoltage"] = pos.battery_level
            elif mp.decoded.portnum == ENVIRONMENTAL_MEASUREMENT_APP:
                env = environmental_measurement_pb2.EnvironmentalMeasurement()
                env.ParseFromString(mp.decoded.payload)
                print(f"->'{env}'")
                if env.barometric_pressure > 0:
                    client.publish(self.prefix+str(getattr(mp, "from"))+"/pressure", env.pressure)
                    if str(getattr(mp, "from")) in self.current_data:
                        self.current_data[str(getattr(mp, "from"))]["pressure"] = env.pressure
                if env.temperature > 0:
                    client.publish(self.prefix+str(getattr(mp, "from"))+"/temperature", env.temperature)
                    if str(getattr(mp, "from")) in self.current_data:
                        self.current_data[str(getattr(mp, "from"))]["temperature"] = env.temperature
                if env.relative_humidity > 0:                    
                    client.publish(self.prefix+str(getattr(mp, "from"))+"/relative_humidity", env.relative_humidity)
                    if str(getattr(mp, "from")) in self.current_data:
                        self.current_data[str(getattr(mp, "from"))]["humidity"] = env.relative_humidity
            elif mp.decoded.portnum == portnums_pb2.NODEINFO_APP:
                info = mesh_pb2.User()
                info.ParseFromString(mp.decoded.payload)
                print(f"->'{info}'")
                print(f"--> '{MessageToJson(info)}'")
                client.publish(self.prefix+str(getattr(mp, "from"))+"/user", MessageToJson(info))

                if not str(getattr(mp, "from")) in self.current_data:
                    self.current_data[str(getattr(mp, "from"))] = {}
                
                self.current_data[str(getattr(mp, "from"))]["shortName"] = info.short_name
                self.current_data[str(getattr(mp, "from"))]["longName"] = info.long_name
                
                print('------------------ CALL DB STR ------------------')
                data_list = [info.short_name, info.long_name]
                self.calldict[str(getattr(mp, "from"))] = data_list
                print(self.calldict)
                #json_object = json.dumps(self.calldict, indent = 4)
                #print(json_object)
                with open("calldb.json", "w") as outfile:
                    json.dump(self.calldict, outfile)
                print('------------------ CALL DB END ------------------')
            elif mp.decoded.portnum == portnums_pb2.TEXT_MESSAGE_APP:
                text = {
                    "message": mp.decoded.payload.decode("utf-8"),
                    "from": getattr(mp, "from"),
                    "to": mp.to
                }
                client.publish(self.prefix+str(getattr(mp, "from"))+"/text_message", json.dumps(text))

        client.subscribe(self.topic)
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
