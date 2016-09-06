/*
 *  This sketch sends a message to a TCP server
 *
 */

#include <ESP8266WiFi.h>
#include <ESP8266WiFiMulti.h>

ESP8266WiFiMulti WiFiMulti;

void setup() {
    Serial.begin(115200);
    delay(10);

    // We start by connecting to a WiFi network
    WiFiMulti.addAP("NETIASPOT-52CC50", "c2svzibeu6i5");

    Serial.println();
    Serial.println();
    Serial.print("Wait for WiFi... ");

    while(WiFiMulti.run() != WL_CONNECTED) {
        Serial.print(".");
        delay(500);
    }

    Serial.println("");
    Serial.println("WiFi connected");
    Serial.println("IP address: ");
    Serial.println(WiFi.localIP());

    delay(500);
}


void loop() {
    const uint16_t port = 8000;
    const char * host = "192.168.1.9"; // ip or dns

    
    
    Serial.print("connecting to ");
    Serial.println(host);

    // Use WiFiClient class to create TCP connections
    WiFiClient client;

    if (!client.connect(host, port)) {
        Serial.println("connection failed");
        Serial.println("wait 5 sec...");
        delay(5000);
        return;
    }

    String data = "";
    char bb0 = 1;
    char bb1 = 195;
    char bb2 = 1;
    char bb3 = 255;
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
    char bb21 = 10;
    char bb22 = 179;
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
    data += bb21;
    data += bb22;
    data += '\r';
    // This will send the request to the server
    client.print(data);

    //read back one line from server
  while(client.available()){
    String line = client.readStringUntil('\r');
    Serial.print(line);
  }

    Serial.println("closing connection");
    client.stop();
    
    Serial.println("wait 5 sec...");
    delay(5000);
}

