//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
String SERVER(String m_data,String url){
String rev;
int i;
unsigned short crc;
int test[m_data.length()];

for(i=0;i<m_data.length();i++){test[i]=int(m_data[i]);} //ładowanie stringa do tablicy

DynamicJsonBuffer jsonBuffer;
JsonObject& root = jsonBuffer.createObject();
JsonArray& pack = root.createNestedArray("data");
        
//for(i=0;i<m_data.length();i++){pack.add(m_data[i]);} //ładowanie stringa do dzejsona
for(i=0;i<m_data.length();i++){pack.add(test[i]);} //ładowanie stringa do dzejsona


//root["DATA"]=(int)m_data;
crc=MAKE_CRC(m_data);
pack.add(highByte(crc));
pack.add(lowByte(crc));

      HTTPClient http;
        http.begin(url); //HTTP
        http.addHeader("Content-Type", "application/x-www-form-urlencoded");
        String output;
        root.printTo(output);
        int httpCode = http.POST(output);
        if(httpCode > 0) {
            SERVER_SD=1;
            if(httpCode == HTTP_CODE_OK) {
                String payload = http.getString();
                String package = "";
                  for (int i=0; i<payload.length(); i++)
                  {
                    if (payload[i]== 'p')
                    {
                      break;
                    }
                    package += payload[i];
                  }
                  rev=package;

            }
        } else {SERVER_SD=0;}
http.end();
return rev;
}
//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
unsigned short MAKE_CRC(String d_crc_make){
  unsigned short rev;
  crc.clearCrc();
  for (int i=0; i<d_crc_make.length(); i++){crc.updateCrc(d_crc_make.charAt(i));}

  rev=crc.getCrc();
  return rev;
}
//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
void SET_IO(int m_id,String m_data){
int var_on[3];
int var_off[3];
boolean ou;
boolean en;
char input[1024];
int value[300];
char number;
String byte_value= "";
int i = 0;
int k = 0;
Serial.println(m_data);
 strcpy(input, m_data.c_str());
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
     byte_value +=number;
    }
    i++;
   }

var_on[0]=highByte(m_id);
var_on[1]=lowByte(m_id);
var_on[2]=0x01;

var_off[0]=highByte(m_id);
var_off[1]=lowByte(m_id);
var_off[2]=0x00;

for (i=0;i<k-2;i++)
  {
  if((value[i]==var_on[0])&&(value[i+1]==var_on[1])&&(value[i+2]==var_on[2])){en=1;ou=1;}
  if((value[i]==var_off[0])&&(value[i+1]==var_off[1])&&(value[i+2]==var_off[2])){en=1;ou=0;} 
  }

if ((en)&&(ou)){out(1);}
if ((en)&&(!ou)){out(0);}
}
//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
void GET_ID_FROM_PACK(String m_data){
 int i;
 int n;
 for(i=0;i<(m_data.length()/2);i++){
 n=m_data.charAt(i);
 n+=m_data.charAt(i+1);
 ID[i]=n;
 }
}

void GET_VAL_FROM_SERVER(){
int var_on[3];
int var_off[3];
boolean ou;
boolean en;
char input[1024];
int value[300];
char number;
String byte_value= "";
int i = 0;
int k = 0;
String m_data;     
String m_trans;  
   
     if(diag){Serial.println("CONN TO SERVER FOR DATA SET...");}    
      m_trans=(char)highByte(MY_ID);
      m_trans+=(char)lowByte(MY_ID);
      m_trans+=(char)0x80;
      if(diag){Serial.println("MY DATA FOR SERVER");}
      if(diag){Serial.println(TR_DATA);}
      m_data=SERVER(m_trans,SERVER_CONF_URL);
      if(SERVER_SD){
      if(diag){Serial.println(m_data);}

        strcpy(input, m_data.c_str());
        while (input[i] != NULL)
        {
           number = input[i];
           if (number == ':')
         {
           value[k] = byte_value.toInt();
           byte_value = "";
           k ++;
         }else{
           byte_value +=number;
         }
        i++;
       }
       for (i=0;i<(k-2)/2;i++){ 
        ID[i]=value[i];
        ID[i]=value[i+1];
       }
       
        if(diag){
         for (i=0;i<(k-2)/2;i++){ 
          Serial.println("ID: ");
          Serial.println(ID[i]);
         }             
        }  
      if(diag){Serial.println("DONE");}
      if(diag){Serial.println();}            
      if(diag){Serial.println();}
      SERVER_CONN_DATA_STATUS=1; 
      }else{
      if(diag){Serial.println("ERROR");}
      if(diag){Serial.println();}            
      if(diag){Serial.println();}
      SERVER_CONN_DATA_STATUS=0; 
      }      
}





