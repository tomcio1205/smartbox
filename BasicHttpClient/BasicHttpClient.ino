/**
 * BasicHTTPClient.ino
 *
 *  Created on: 24.05.2015
 *
 */

#include <Arduino.h>

#include <ESP8266WiFi.h>
#include <ESP8266WiFiMulti.h>
#include "Crc16.h"
#include <ESP8266HTTPClient.h>

#define USE_SERIAL Serial

Crc16 crc; 

ESP8266WiFiMulti WiFiMulti;

String data = "";
char bb0 = 1;
char bb1 = 195;
char bb2 = 1;
char bb3 = 144;
char bb4 = 4;
char bb5 = 226;
char bb6 = 230;
char bb7 = 1;
char bb8 = 196;
char bb9 = 1;
char bb10 = 255;
char bb11 = 4;
char bb12 = 226;
char bb13 = 230;
char bb14 = 1;
char bb15 = 197;
char bb16 = 1;
char bb17 = 255;
char bb18 = 4;
char bb19 = 226;
char bb20 = 230;

void setup() {

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

//    WiFiMulti.addAP("NETIASPOT-52CC50", "c2svzibeu6i5");
    WiFiMulti.addAP("NETIASPOT-B87D10", "8k3zs5aomf7z");

}

void loop() {
    // wait for WiFi connection
    if((WiFiMulti.run() == WL_CONNECTED)) {

        HTTPClient http;
        data="";
        data="";
        data += bb0;
        data += bb1;
        data += bb2;
        data += bb3;
        data += bb4;
        data += bb5;
        data += bb6;
        data += bb7;
        data += bb8;
        data += bb9;
        data += bb10;
        data += bb11;
        data += bb12;
        data += bb13;
        data += bb14;
        data += bb15;
        data += bb16;
        data += bb17;
        data += bb18;
        data += bb19;
        data += bb20;
        crc.clearCrc();
        for (int i=0; i<data.length(); i++)
        {
          crc.updateCrc((int)data[i]);
        }
        unsigned short value = crc.getCrc();
      //  Serial.print("Checksum ");
      //  Serial.println(value, HEX);
        //////////////////calculate crc16//////////////////
        data += (char)highByte(value);
        data += (char)lowByte(value); 

        USE_SERIAL.print("[HTTP] begin...\n");
        // configure traged server and url
        //http.begin("https://192.168.1.12/test.html", "7a 9c f4 db 40 d3 62 5a 6e 21 bc 5c cc 66 c8 3e a1 45 59 38"); //HTTPS
        http.begin("http://192.168.1.9:8880/smartbox"); //HTTP

        USE_SERIAL.print("[HTTP] GET...\n");
        // start connection and send HTTP header
        http.addHeader("Content-Type", "application/x-www-form-urlencoded");
        int httpCode = http.POST(data);
//        int httpCode = http.GET();

        // httpCode will be negative on error
        if(httpCode > 0) {
            // HTTP header has been send and Server response header has been handled
            USE_SERIAL.printf("[HTTP] GET... code: %d\n", httpCode);

            // file found at server
            if(httpCode == HTTP_CODE_OK) {
                String payload = http.getString();
                USE_SERIAL.println(payload);
                  for (int i=0; i<payload.length(); i++)
                  {
                    if (payload[i] == '<')
                    {
                      break;
                    }
                    USE_SERIAL.print("Value of byte number ");
                    USE_SERIAL.print(i);
                    USE_SERIAL.print(" : ");
                    USE_SERIAL.println(payload[i], HEX);
                  }
            }
        } else {
            USE_SERIAL.printf("[HTTP] GET... failed, error: %s\n", http.errorToString(httpCode).c_str());
        }

        http.end();
    }

    delay(10000);
}

