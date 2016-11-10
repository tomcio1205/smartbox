/**
 * BasicHTTPClient.ino
 *
 *  Created on: 24.05.2015
 *
 */

#include <Arduino.h>
#include <stdlib.h>
#include <ESP8266WiFi.h>
#include <ESP8266WiFiMulti.h>
#include "Crc16.h"
#include <ArduinoJson.h>
#include <ESP8266HTTPClient.h>

#define USE_SERIAL Serial
#define f_key_configuration_package 128
#define f_key_next_willbe_configuration 64
#define f_key_send_report 16
#define f_key_make_reset_low 4
#define f_key_make_reset_high 5
#define f_key_make_alarm_reset 2
#define f_key_output_state_high 1
#define f_key_output_state_low 0

//#define ARRAY_SIZE 32
Crc16 crc; 

ESP8266WiFiMulti WiFiMulti;

//byte byteArray[ARRAY_SIZE];

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
char bb20 = 1;

//byte b0 = 1;
//byte b1 = 195;
//byte b2 = 1;
//byte b3 = 144;
//byte b4 = 4;
//byte b5 = 226;
//byte b6 = 230;
//byte b7 = 1;
//byte b8 = 196;
//byte b9 = 1;
//byte b10 = 255;
//byte b11 = 4;
//byte b12 = 226;
//byte b13 = 230;
//byte b14 = 1;
//byte b15 = 197;
//byte b16 = 1;
//byte b17 = 255;
//byte b18 = 4;
//byte b19 = 226;
//byte b20 = 0;

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

//        byteArray[0] = 1;
//        byteArray[1] = 255;
//        byteArray[2] = 12;
//        byteArray[3] = 144;
//        byteArray[4] = 0;
        DynamicJsonBuffer jsonBuffer;
        JsonObject& root = jsonBuffer.createObject();
        JsonArray& dataa = root.createNestedArray("data");
        root["sensor"] = "gps";
        root["time"] = 1351824120;
//        dataa.add(48.756080, 6);  // 6 is the number of decimals to print
//        dataa.add(2.302038, 6);   // if not specified, 2 digits are printed
        dataa.add(2);
        dataa.add(3);
        dataa.add(4);
        root.printTo(Serial);
        crc.clearCrc();
        for (int i=0; i<data.length(); i++)
        {
//          USE_SERIAL.println(int(0), HEX);
          crc.updateCrc(data[i]);
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
        http.begin("http://192.168.1.7:8880/smartbox"); //HTTP

        USE_SERIAL.print("[HTTP] GET...\n");
        // start connection and send HTTP header
        http.addHeader("Content-Type", "application/x-www-form-urlencoded");
        String output;
        root.printTo(output);
        int httpCode = http.POST(output);
//        int httpCode = http.GET();

        // httpCode will be negative on error
        if(httpCode > 0) {
            // HTTP header has been send and Server response header has been handled
            USE_SERIAL.printf("[HTTP] GET... code: %d\n", httpCode);

            // file found at server
            if(httpCode == HTTP_CODE_OK) {
                String payload = http.getString();
                //get only package from response
                //'1:195:1:144:1:196:0:255:1:197:0:255:110:92:p'
                String package = "";
                  for (int i=0; i<payload.length(); i++)
                  {
                    if (payload[i]== 'p')
                    {
                      break;
                    }
                    package += payload[i];
                  }
                  char input[1024];
                  // if size of value array is big exception was thrown, we must check this
                  // try with reserve memory with malloc or other??
                  int value[300];
                  char number;
                  String byte_value= "";
                  int i = 0;
                  int k = 0;
                  strcpy(input, package.c_str());
                  while (input[i] != NULL)
                  {
                    number = input[i];
                    
                    if (number == ':')
                    {
                      value[k] = byte_value.toInt(); 
                      byte_value = "";
                      k ++;
                    }
                    else
                    {
                      byte_value += number;                                                
                    }
                    i++;
                  }
//                for (int i=0; i<k; i++)
//                {
//                  USE_SERIAL.println(value[i]);             
//                }
                  if (value[2] == f_key_make_reset_low || value[2] == f_key_make_reset_high)
                  {
                    digitalWrite(12, LOW);
                    delay(100);
                    digitalWrite(12, HIGH);
                    delay(100);
                    digitalWrite(12, LOW);
                    delay(100);
                    digitalWrite(12, HIGH);
                    delay(100);
                    digitalWrite(12, LOW);
                    delay(100);
                    digitalWrite(12, HIGH);
                    delay(100);
                    digitalWrite(12, LOW);                      
                                        
                  }
                  if (value[2] == f_key_output_state_high || value[2] == f_key_make_reset_high)
                  {
                    USE_SERIAL.println("Set high");
                    digitalWrite(12, HIGH);
                  }
                  if (value[2] == f_key_output_state_low || value[2] == f_key_make_reset_low)
                  {
                    USE_SERIAL.println("Set low");
                    digitalWrite(12, LOW);
                  }

            }
        } else {
            USE_SERIAL.printf("[HTTP] GET... failed, error: %s\n", http.errorToString(httpCode).c_str());
        }
        http.end();
    }
    

    delay(1000);
}

