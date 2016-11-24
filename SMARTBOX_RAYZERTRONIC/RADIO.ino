///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
void WIFI_INIT(String m_ssid,String m_pass){

   const char* ma_ssid=m_ssid.c_str();
   const char* ma_pass=m_pass.c_str();

 //  WiFiMulti.addAP(ma_ssid, ma_pass);
   WiFi.begin(ma_ssid, ma_pass);
}
///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
void WIFI_CLEAR(){WiFi.disconnect(); }//WiFiMulti.APlistClean();
///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
boolean WIFI_ONLINE(){
//if(((WiFiMulti.run()) == (WL_CONNECTED))){return 1;}else{return 0;}
if((WiFi.status() == WL_CONNECTED)){return 1;}else{return 0;}
}
///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
String BT_INIT(String NAME,boolean A){  
String Y;
String AT;
int i;
String mac_adr;
String AT1="";
Y="";
Serial.print("AT");//sprawdzanie obecności
while((Y.indexOf("OK")) == (-1)){Y=Serial.readString();} 
Y="";
Serial.print("AT+SHOW1");//Ustawienie widoczności
while((Y.indexOf("OK+Set:1")) == (-1)){Y=Serial.readString();} 
Y="";
Serial.print("AT+NOTI1");//Ustawienie notyfikacji
while((Y.indexOf("OK+Set:1")) == (-1)){Y=Serial.readString();} 
Y="";
if(A){AT1="AT+IMME1";}else{AT1="AT+IMME0";}
Serial.print(AT1);
if(A){while(Y.indexOf("OK+Set:1") == -1){Y=Serial.readString();} }else{while(Y.indexOf("OK+Set:0") == -1){Y=Serial.readString();} }    
Y="";
AT="AT+NAMEMESH-";
AT+=NAME;
Y="";
Serial.print(AT);//ustawnienie nazwy
while(Y.indexOf("OK") == -1){Y=Serial.readString();} 
Y="";
Serial.print("AT+ADDR?");//Sprawdzanie własnego MAC
while(Y.indexOf("OK+LADD:")== -1){Y=Serial.readString();} 
//wpisanie adresu MAC do pamięci
mac_adr="";
for(i=8;i<21;i++){mac_adr+=Y.charAt(i);} 
Y="";
delay(1500);
Serial.print("AT+RESET");//reset BT
while(Y.indexOf("OK+RESET")== -1){Y=Serial.readString();Serial.print(Y);} 
Y="";
 return mac_adr;
}
///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
void BT_MODE(boolean A){
String AT2="";
String Y="";
if(A){AT2="AT+ROLE1";}else{AT2="AT+ROLE0";}
Serial.print(AT2);
if(A){while(Y.indexOf("K+Set:1") == -1){Y=Serial.readString();} }else{while(Y.indexOf("K+Set:0") == -1){Y=Serial.readString();} }   
}
