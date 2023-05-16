# python3.6

import meshtastic_mqtt_aprs.portnums_pb2 as portnums_pb2
from meshtastic_mqtt_aprs.portnums_pb2 import ENVIRONMENTAL_MEASUREMENT_APP, POSITION_APP

import random
import json

import aprslib
from datetime import datetime

import meshtastic_mqtt_aprs.mesh_pb2 as mesh_pb2
import meshtastic_mqtt_aprs.mqtt_pb2 as mqtt_pb2
import meshtastic_mqtt_aprs.environmental_measurement_pb2 as environmental_measurement_pb2

from paho.mqtt import client as mqtt_client

import requests
from paho.mqtt import client as mqtt_client
from google.protobuf.json_format import MessageToJson

#uncomment for AppDaemon
#import hassapi as hass

#swap for AppDaemon
#class MeshtasticMQTT(hass.Hass=None):
class MeshtasticMQTT():

    broker = ''
    username = ''
    password = ''
    port = 1883
    topic = "msh/2/c/#"
    # generate client ID with pub prefix randomly
    client_id = f'meshtastic-mqtt-{random.randint(0, 100)}'
    
    prefix = "meshtastic/"

    aprsCall = ''
    aprsHost = ''
    aprsPort = '14580'
    aprsPass = ''
    aprsTable = '/'
    aprsSymbol = '`'
    
    # Id -> Callsign DB
    calldict = {
    }
    
    print("Loading CallDB...")
    try:
        with open('calldb.json') as json_file:
            calldict = json.load(json_file)
    except:
        print("calldb.json not found")
    print(calldict)
    
    from pathlib import Path
    print(Path.cwd())

    def connect_mqtt(self) -> mqtt_client:
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                print("(GO) Connected to MQTT Broker!")
            else:
                print("(GO) Failed to connect, return code %d\n", rc)

        client = mqtt_client.Client(self.client_id)
        client.username_pw_set(self.username, self.password)
        client.on_connect = on_connect
        client.connect(self.broker, self.port)
        return client


    def subscribe(self, client: mqtt_client):
        def on_message(client, userdata, msg):
            #print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
            se = mqtt_pb2.ServiceEnvelope()
            se.ParseFromString(msg.payload)

            print(se)
            mp = se.packet

            if mp.decoded.portnum == portnums_pb2.POSITION_APP:
                pos = mesh_pb2.Position()
                pos.ParseFromString(mp.decoded.payload)
                print(getattr(mp, "from"))
                print(pos)
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
                                snr = 'n/a'
                            rssi = str(mp.priority)
                            if mp.priority == 0:
                                rssi = 'n/a'
                            Comment = 'MeshTastic ' + self.calldict[str(getattr(mp, "from"))][1] + ' SNR: ' + snr + ' dB RSSI: ' + rssi + ' dBm' # add long name from DB

                            # MESSAGEpacket = f'{self.aprsCall}>APZ32E,WIDE1-1:={Latitude}{LatitudeNS}\{Longitude}{LongitudeEW}S{Comment}\n'
                            MESSAGEpacket = f'{self.aprsCall}>APZ32E,WIDE1-1:;{DestCallsign}*{TimeStamp}z{Latitude}{LatitudeNS}{self.aprsTable}{Longitude}{LongitudeEW}{self.aprsSymbol}{Comment}\n'
                            print('Sending message')
                            print(MESSAGEpacket)

                            try:
                                AIS.sendall(MESSAGEpacket)
                                AIS.close()
                            except:
                                print("An exception occurred")
                    else:
                        print("(CALL DB) Call is NOT in DB, skip APRS upload")
                #lets also publish the battery directly
                if pos.battery_level > 0:
                    client.publish(self.prefix+str(getattr(mp, "from"))+"/battery", pos.battery_level)
            elif mp.decoded.portnum == ENVIRONMENTAL_MEASUREMENT_APP:
                env = environmental_measurement_pb2.EnvironmentalMeasurement()
                env.ParseFromString(mp.decoded.payload)
                print(env)
                client.publish(self.prefix+str(getattr(mp, "from"))+"/temperature", env.temperature)
                client.publish(self.prefix+str(getattr(mp, "from"))+"/relative_humidity", env.relative_humidity)
            elif mp.decoded.portnum == portnums_pb2.NODEINFO_APP:
                info = mesh_pb2.User()
                info.ParseFromString(mp.decoded.payload)
                #print(MessageToJson(info))
                client.publish(self.prefix+str(getattr(mp, "from"))+"/user", MessageToJson(info))
                
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
