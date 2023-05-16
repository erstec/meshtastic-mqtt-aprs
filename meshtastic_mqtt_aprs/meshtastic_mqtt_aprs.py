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
                            # traccarURL = "http://"+self.traccarHost+":5055?id="+str(getattr(mp, "from"))+"&lat="+str(pos.latitude_i * 1e-7)+"&lon="+str(pos.longitude_i * 1e-7)+"&altitude="+str(pos.altitude)+"&battery_level="+str(pos.battery_level)+"&hdop="+str(pos.PDOP)+"&accuracy="+str(pos.PDOP*0.03)
                            # print(traccarURL)
                            # submitted = requests.get(traccarURL)
                            # print(submitted)
                            try:
                                AIS = aprslib.IS(self.aprsCall, passwd=self.aprsPass, host=self.aprsHost, port=self.aprsPort)
                                AIS.connect()
                            except:
                                print("An exception occurred")
                            # send a single message
                            # LY1BWB-10>APMI06,TCPIP*,qAC,T2CAEAST:@160706z5443.89N\02515.72E-Slava Ukraini!
                            
                            # LY3PH-10>APZ32E,WIDE1-1:=5441.06N/02511.91E&DEVEL ESP IG github.com/erstec/APRS-ESP
                            # LY3PH-10>APZ32E,TCPIP*,qAC,T2CZECH:=5441.06N/02511.91E&DEVEL ESP IG github.com/erstec/APRS-ESP
                            
                            # sprintf(strtmp, "%s-%d>APZ32E", config.aprs_mycall, config.aprs_ssid);
                            # tnc2Raw += ",";
                            # tnc2Raw += String(config.aprs_path);
                            # tnc2Raw += ":";
                            # tnc2Raw += String(loc);
                            # tnc2Raw += String(config.aprs_comment);
                            # sprintf(loc, "=%02d%02d.%02dN%c%03d%02d.%02dE%c", 
                            #   lat_dd, lat_mm, lat_ss, config.aprs_table, lon_dd, lon_mm, lon_ss, config.aprs_symbol);

                            DestCallsign = self.calldict[str(getattr(mp, "from"))]
                            DestCallsign = DestCallsign + "-M"
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
                            
                            d = cdeg
                            m = cmin
                            s = csec
                            
                            #m, s = divmod(abs(deg)*3600, 60)
                            #d, m = divmod(m, 60)
                            #if deg < 0:
                            #    d = -d
                            #d, m = int(d), int(m)
                            print(d)
                            print(m)
                            print(s)
                            Latitude = "%02d%02d.%02d" % (d, m, s)
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
                            
                            d = cdeg
                            m = cmin
                            s = csec
                            
                            #m, s = divmod(abs(deg)*3600, 60)
                            #d, m = divmod(m, 60)
                            #if deg < 0:
                            #    d = -d
                            #d, m = int(d), int(m)
                            print(d)
                            print(m)
                            print(s)
                            Longitude = "%03d%02d.%02d" % (d, m, s)
                            print(Longitude)
                            if deg > 0:
                                LongitudeEW = 'E'
                            else:
                                LongitudeEW = "W"
                            Comment = 'Slava Ukraini!'
                            # MESSAGEpacket = f'{self.aprsCall}>APZ32E,WIDE1-1:={Latitude}{LatitudeNS}\{Longitude}{LongitudeEW}S{Comment}\n'
                            MESSAGEpacket = f'{self.aprsCall}>APZ32E,WIDE1-1:;{DestCallsign}*{TimeStamp}z{Latitude}{LatitudeNS}\{Longitude}{LongitudeEW}S{Comment}\n'
                            print('Sending message')
                            print(MESSAGEpacket)
                            AIS.sendall(MESSAGEpacket)
                            AIS.close()
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
                
                print('------------------ INFO STR ------------------')
                print(info)
                print(MessageToJson(info))
                print(info.short_name)
                print('------------------ INFO END ------------------')
                
                print('------------------ CALL DB STR ------------------')
                self.calldict[str(getattr(mp, "from"))] = info.short_name
                print(self.calldict)
                json_object = json.dumps(self.calldict, indent = 4)
                print(json_object)
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
