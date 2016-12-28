/**
 * BasicHTTPClient.ino
 *
 *  Created on: 24.05.2015
 *
 */

#include <Arduino.h>
#include <stdlib.h>
#include <ESP8266WiFiMulti.h>
#include "Crc16.h"
#include <ArduinoJson.h>
#include <ESP8266HTTPClient.h>
////////////////////
#include <ESP8266HTTPClient.h>
#include <ESP8266httpUpdate.h>
/////////////////////////
#define USE_SERIAL Serial
#define f_key_configuration_package 128
#define f_key_next_willbe_configuration 64
#define f_key_send_report 16
#define f_key_make_reset_low 4
#define f_key_make_reset_high 5
#define f_key_make_alarm_reset 2
#define f_key_output_state_high 1
#define f_key_output_state_low 0

#define LOCAL_SERVER "http://192.168.1.103:8080/smartbox/work"
#define REMOTE_SERVER "http://51.255.162.139:8080/smartbox/work"
#define SKETCH_BIN "http://192.168.1.103/httpUpdate.ino.bin"
#define VERSION_SKETCH  "v1_11"
#define MY_ID "7a2dfe63-165d-4029-9d20-069c90a148ba"
#define BOOT_AFTER_UPDATE false
//#define ARRAY_SIZE 32
Crc16 crc;

ESP8266WiFiMulti WiFiMulti;

//byte byteArray[ARRAY_SIZE];

String data = "12345323";
char x = '2';

int package[] = {1,195,1,144,4,226,230,1,196,1,255,4,226,230,1,197,1,255,4,226,1};
int bb0 = 1;
int bb1 = 195;
int bb2 = 1;
int bb3 = 144;
int bb4 = 4;
int bb5 = 226;
int bb6 = 230;
int bb7 = 1;
int bb8 = 196;
int bb9 = 1;
int bb10 = 255;
int bb11 = 4;
int bb12 = 226;
int bb13 = 230;
int bb14 = 1;
int bb15 = 197;
int bb16 = 1;
int bb17 = 255;
int bb18 = 4;
int bb19 = 226;
int bb20 = 1;
boolean should_update = true;
int array_size = sizeof(package)/sizeof(package[0]);

void setup() {

    pinMode(12, OUTPUT);


    USE_SERIAL.begin(115200);
   // USE_SERIAL.setDebugOutput(true);

    USE_SERIAL.println();
    USE_SERIAL.println();
    USE_SERIAL.println();

    for(uint8_t t = 4; t > 0; t--) {
        USE_SERIAL.printf("[SETUP] WAIT %d...\n", t);
        USE_SERIAL.flush();
        delay(1000);
    }

//    WiFiMulti.addAP("WN-696969", "N0M0n3yN0wifi");
    // WiFiMulti.addAP("NETIASPOT-52CC50", "c2svzibeu6i5");
//    WiFiMulti.addAP("NETIASPOT-B87D10", "8k3zs5aomf7z");
   WiFiMulti.addAP("RES_SOLUTION_313", "P@$$r3$s");
}

void loop() {
    // wait for WiFi connection
    // if (!activateOta) {
      if((WiFiMulti.run() == WL_CONNECTED)) {
        HTTPClient http;
          DynamicJsonBuffer jsonBuffer;
          JsonObject& my_json = jsonBuffer.createObject();
          JsonObject& my_json2 = jsonBuffer.createObject();
          JsonObject& root = jsonBuffer.createObject();
          JsonArray& data = root.createNestedArray("data");
          my_json["ID"] = "7a2dfe63-165d-4029-9d20-069c90a148ba";
          my_json["PowerConsumption"] = 234.23;
          my_json2["ID"] = "48f272be-d4a2-4e51-b20c-8c11b4bc9b4e";
          my_json2["PowerConsumption"] = 434.63;
          my_json.printTo(Serial);

          USE_SERIAL.print("[HTTP] begin...\n");
          // configure traged server and url
          //http.begin("https://192.168.1.12/test.html", "7a 9c f4 db 40 d3 62 5a 6e 21 bc 5c cc 66 c8 3e a1 45 59 38"); //HTTPS
          http.begin(LOCAL_SERVER); //HTTP

          USE_SERIAL.print("[HTTP] GET...\n");
          // start connection and send HTTP header
          http.addHeader("Content-Type", "application/x-www-form-urlencoded");
          //set sdk version in header
          http.addHeader("SDK Version", VERSION_SKETCH);
          String output;
          my_json.printTo(output);
          data.add(output);
          String output2;
          my_json2.printTo(output2);
          data.add(output2);
          String root_output;
          root.printTo(root_output);
          int httpCode = http.POST(root_output);
  //        int httpCode = http.GET();

          // httpCode will be negative on error
          if(httpCode > 0) {
              // HTTP header has been send and Server response header has been handled
              USE_SERIAL.printf("[HTTP] GET... code: %d\n", httpCode);

              // file found at server
              if(httpCode == HTTP_CODE_OK) {
                  String payload = http.getString();
                  char json[payload.length()];

                  //get only package from response
                    for (int i=0; i<payload.length(); i++)
                    {
                      json[i]= payload[i];
                    }
                    JsonObject& root2 = jsonBuffer.parseObject(json);
  //                  root2.printTo(Serial);
                    int count_devices = root2["CountDevice"];

                    for (int i=0; i<=count_devices; i++)
                    {
                      char c[3];
                      sprintf(c, "%d", i);
                      String id = root2[c]["ID"];

                      USE_SERIAL.println(id);
                      if (id ==  MY_ID)
                      {
                        String IsON = root2[c]["IsOn"];
                        USE_SERIAL.print("Should I on? ");
                        USE_SERIAL.println(IsON);
                        should_update = root2[c]["ShouldUpdate"];
                        String sdk_version = root2[c]["SdkVersion"];
                        USE_SERIAL.print("Activate OTA? ");
                        USE_SERIAL.println(should_update);
                        if (should_update)
                        {
                          USE_SERIAL.println("Should Update");
                          // ESPhttpUpdate.rebootOnUpdate(BOOT_AFTER_UPDATE);
                          t_httpUpdate_return ret = ESPhttpUpdate.update(SKETCH_BIN);
                          switch(ret) {
                             case HTTP_UPDATE_FAILED:
                                 USE_SERIAL.printf("HTTP_UPDATE_FAILED Error (%d): %s\n", ESPhttpUpdate.getLastError(), ESPhttpUpdate.getLastErrorString().c_str());
                                 break;

                             case HTTP_UPDATE_NO_UPDATES:
                                 USE_SERIAL.println("HTTP_UPDATE_NO_UPDATES");
                                 break;

                             case HTTP_UPDATE_OK:
                                 USE_SERIAL.println("HTTP_UPDATE_OK");
                                 break;

                             default:
                                 USE_SERIAL.print("Undefined HTTP_UPDATE Code: ");
                                 USE_SERIAL.println(ret);

                          }
                        }
                        else
                        {
                          USE_SERIAL.println("Should not Update");
                        }
                        USE_SERIAL.println(sdk_version);
                      }
                    }
                  }
                } else {
                  USE_SERIAL.printf("[HTTP] GET... failed, error: %s\n", http.errorToString(httpCode).c_str());
                }
          http.end();
      }
      delay(1000);
}