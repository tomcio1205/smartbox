//oprogramowanie do Smartboxa w wersji multi 
//2016r
#include <EEPROM.h>
#include <ESP8266WiFi.h>

#include "Crc16.h"
//#include <ESP8266WiFiMulti.h>
#include <ESP8266HTTPClient.h>
#include <ArduinoJson.h>

#define  led_pin 14//dla SMARTBOX TURBO
#define  pk_pin 12

//#define  led_pin 2//dla DEV BOARD
//#define  pk_pin 16


Crc16 crc;

//ESP8266WiFiMulti WiFiMulti;
HTTPClient http;


//zmienne globalne
String SERVER_URL="http://51.255.162.139:8880/smartbox/work";
String SERVER_CONF_URL="http://51.255.162.139:8880/smartbox/configuration";
//String SERVER_URL="http://192.168.2.107:8880/smartbox/work";
//String SERVER_CONF_URL="http://192.168.2.107:8880/smartbox/configuration";
String MY_MAC;
String WIFI_SSID;//="WN-696969";
String WIFI_PASS;//="N0M0n3yN0wifi";
//int MY_ID=0x01c3;//czajnik
//int MY_ID=0x01c4;//swiatło
int MY_ID=0x01c5;//gniazdko
int ID[64];
boolean MODE=1;//to mam pobierać z eeprom-do zrobienia
boolean SERVER_SD;//czy serwer odesłał jakieś dane
String REV_DATA;
String TR_DATA;
String MESH_REV;
int VAR_AMP;
boolean diag=1;
boolean WIFI_STATUS;
boolean SERVER_CONN_DATA_STATUS;


int ANAL(int,int);
void led(int, int);
void out(boolean);
void CLEAR_EEPROM();
String GET_SSID();
String GET_PASS();
void SET_PASS(String);
void SET_SSID(String);
void MAP_MESH();
String MESH_MASTER(String);
String MESH_SLAVE(String);
void WIFI_INIT(String,String);
String BT_INIT(String,boolean);
String SERVER(String,String);
unsigned short MAKE_CRC(String);
void SET_IO(int,String);
void GET_ID_FROM_PACK(String);
void WIFI_CLEAR();
boolean WIFI_ONLINE();
void GET_VAL_FROM_SERVER();
void BT_MODE(boolean);






void setup() {
int i;  
//deklaracja wyjść
pinMode(led_pin, OUTPUT);//led
pinMode(pk_pin, OUTPUT);
Serial.begin(9600);
Serial.print(" "); //czyszczenie uarta
out(0);
led(100,1);

//wifi z eepromem
//EEPROM.begin(512);
//WIFI_SSID=GET_SSID();
//WIFI_PASS=GET_PASS();
WIFI_SSID="Dom";
WIFI_PASS="bartek97";
if(diag){Serial.println(WIFI_SSID);}
if(diag){Serial.println(WIFI_PASS);}
//if(!MODE){WIFI_CLEAR();}//jestem slave to rolacz
if(MODE){WIFI_INIT(WIFI_SSID,WIFI_PASS);};//jeśli jestem masterem to łacz
led(100,1);

//konfiguracja BT
//MY_MAC=BT_INIT("TEST",1);//inicjacja BT
if(diag){Serial.println(MY_MAC);}
//BT_MODE(MODE);
led(200,2);
MAP_MESH();//prerenderowanie sieci mesh
led(100,3);
}

void loop() {
  if(diag){Serial.println();}
  if (MODE){
   WIFI_STATUS=WIFI_ONLINE(); 
   if(WIFI_STATUS){     
    if(!SERVER_CONN_DATA_STATUS){GET_VAL_FROM_SERVER();}//jesli nie było internetu to pobierz teraz zasoby
    if(diag){Serial.println("MAKE PACK:");}
    TR_DATA="";
    TR_DATA=(char)highByte(MY_ID);
    TR_DATA+=(char)lowByte(MY_ID);
    TR_DATA+=(char)0x01;//normalny tryb pracy
    if(diag){Serial.println(TR_DATA);}
    if(diag){Serial.println("CONN TO SERVER...");}
    REV_DATA=SERVER(TR_DATA,SERVER_CONF_URL);
//    if(diag){Serial.println("REVICE DATA: ");}
//    if(diag){Serial.println(REV_DATA);}
    if(SERVER_SD){MESH_REV=MESH_MASTER(REV_DATA);}//wysyłamy po mesh dane odebrane z serwera-odbieramy zwrotne paczki
    if(SERVER_SD){led(100,1);}else{led(400,1);}//mrygam se diodą
    if(SERVER_SD){SET_IO(MY_ID,REV_DATA);}//ustawiam stan na wyjściu
    
    VAR_AMP=ANAL(20,100);//robię analizę poboru
    if(diag){Serial.println("ANAL_VAR: ");}
    if(diag){Serial.println(VAR_AMP);}
    //składam własną paczkę
    TR_DATA="";
    TR_DATA=(char)highByte(MY_ID);
    TR_DATA+=(char)lowByte(MY_ID);
    TR_DATA+=(char)0x01;//normalny tryb pracy    
    TR_DATA+=(char)highByte(VAR_AMP);
    TR_DATA+=(char)lowByte(VAR_AMP);  
    if(diag){Serial.println("MY_PACK_FOR_SERVER: ");}
    if(diag){Serial.println(TR_DATA);}  
    TR_DATA+=MESH_REV;//dodaję paczkę odebraną z mesh
    if(diag){Serial.println("ALL_DATA_FOR_SERWER: ");}
    if(diag){Serial.println(TR_DATA);}
    REV_DATA=SERVER(TR_DATA,SERVER_URL);  
    if(SERVER_SD){led(100,1);}else{led(400,1);}//mrygam se diodą   
   }else{
   SERVER_CONN_DATA_STATUS=0;  //resetuje flagę aktualnych zasobów z serwera 
   led(500,1);    
   if(diag){Serial.println("wait for wifi...");}   
   }
  }else{

    
  }
}


