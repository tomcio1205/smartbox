#include <ESP8266WiFi.h>
#include "Crc16.h"

Crc16 crc; 

//const char* ssid     = "NETIASPOT-B87D10";
//const char* password = "8k3zs5aomf7z";
const char* ssid     = "NETIASPOT-52CC50";
const char* password = "c2svzibeu6i5";
//const char* ssid     = "WN-696969";
//const char* password = "N0M0n3yN0wifi";
//const char* ssid     = "TP-LINK_9F2BAE";
//const char* password = "qwerty123";
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
//char bb21 = 10;
//char bb22 = 179;

String readString;
void setup() {
  pinMode(13, OUTPUT);
  led(100, 5);
  Serial.begin(115200);
  delay(100);

  // We start by connecting to a WiFi network

  Serial.println();
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}

const uint16_t port = 8000;
const char * host = "192.168.1.9"; // ip or dns

void loop() {
  delay(5000);
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

  // This will send the request to the server
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
//  data += bb21;
//  data += bb22;
  //////////////////calculate crc16///////////////////
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
  client.print(data);
  delay(100);
  String line;
  // Read all the lines of the reply from server and print them to Serial
  while (client.available())
  {
//    int byteBuffer = 12;
//    char interesting[10];
//     int byteCount = client.readBytesUntil('\n', interesting, byteBuffer);

    // Convert the byte array to a String

   
    line = client.readStringUntil('\r');
//    Serial.println(line.length());
//    Serial.println(line);
//    Serial.print(line[2] + " " + line[0]);
  }

//  Serial.println("test");

  for (int i=0; i<line.length(); i++)
  {
    Serial.print("Value of byte number ");
    Serial.print(i);
    Serial.print(" : ");
    Serial.println(line[i], HEX);
  }

  Serial.println();
  Serial.println("closing connection");
  Serial.println();
  client.stop();
}

//funkcja obsługi doidy
void led(int czasled, int ilerazyled) {
  int ledi = 0;
  for (ledi = 0 ; ledi < ilerazyled ; ledi++) {
    digitalWrite(13, HIGH); //Włączenie diody
    delay(czasled);
    digitalWrite(13, LOW); //Wyłączenie diody
    delay(czasled);
  }
}
