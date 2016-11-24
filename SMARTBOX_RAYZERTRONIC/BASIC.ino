int ANAL(int DK,int HW){
  int ret_var;
  int i;
  int j;
  
  int ANAL_BUF[HW];
  int X;
  int Y;

  float sr_max;//na podstawie DK
  float sr_min;
  float ZERO;
  float f_zero_var;
  
  for (i=0;i<=HW;i++){ANAL_BUF[i]=analogRead(A0);} //zbieranie próbek

  for(int i=0;i<=HW;i++){for(int j=1;j<=HW-i;j++){if(ANAL_BUF[j-1]>ANAL_BUF[j]){X=ANAL_BUF[j-1];Y=ANAL_BUF[j];ANAL_BUF[j-1]=Y;ANAL_BUF[j]=X;}}}//sortowanie pomiaru
 
  sr_min=0;
  for(i=0;i<=DK;i++){sr_min+=ANAL_BUF[i];}//zbierz średnią maxymalną
  sr_min=sr_min/(DK+1);
//  Serial.println(sr_min);
  sr_max=0;
  for(i=HW-DK;i<=HW;i++){sr_max+=ANAL_BUF[i];}//zbierz średnią maxymalną
  sr_max=sr_max/(DK+1);
 // Serial.println(sr_max);
  f_zero_var=(sr_max-sr_min)/2;//różnica wartosci jako amplituda dzielona na pół-mamy połowę amplitudy
 // Serial.println(f_zero_var);
  //ZERO=sr_min+f_zero_var;//mamy środek czyli wartosć punktu zerowego sinusa -narazie nie używana w żadnych obliczeniach ponieważ mamy f_zero_var
  //Serial.println(ZERO);
  f_zero_var=f_zero_var*0.976563; //osiągniętą ilość kwantów będącą wartością poboru w kwancie przemnażamy przez wartość rzeczywistego napięcia na jeden kwant-uzyskujemy realną wartość napięcia w mV
 // Serial.println(f_zero_var);
  //f_zero_var=873;//20A-symulacja
  f_zero_var=f_zero_var/0.0215645; //dzielimy wartość napięcia w mV przez stałą 1mA dla 1mV-osiągamy pobór wyrażony w mA 
 // Serial.println(f_zero_var);
  ret_var=f_zero_var*1; //
//  Serial.println(ret_var);
 // Serial.println();
 // if((highByte(m_amp))==255){highByte(m_amp);}
 // if((lowByte(m_amp))==255){lowByte(m_amp)--;}
 
  return ret_var;
}
//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//funkcja obsługi doidy
void led(int czasled, int ilerazyled) {
  int ledi = 0;
  for (ledi = 0 ; ledi < ilerazyled ; ledi++) {
    digitalWrite(led_pin, LOW); //Włączenie diody
    delay(czasled);
    digitalWrite(led_pin, HIGH); //Wyłączenie diody
    delay(czasled);
  }
}

//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//funkcja obsługi przekaźnika
void out(boolean status_przek) {
  if (status_przek == 0) {
    digitalWrite(pk_pin, HIGH);
  } else {
    digitalWrite(pk_pin, LOW);
  }
}
//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////



void CLEAR_EEPROM(){for (int i = 0; i < 512; i++){EEPROM.write(i, 0);} EEPROM.commit();}

String GET_PASS(){
  
  String e_pass; 
  e_pass= (char)EEPROM.read(0);
  e_pass+= (char)EEPROM.read(1);
  e_pass+= (char)EEPROM.read(2);
  e_pass+= (char)EEPROM.read(3);
  e_pass+= (char)EEPROM.read(4);
  e_pass+= (char)EEPROM.read(5);
  e_pass+= (char)EEPROM.read(6);
  e_pass+= (char)EEPROM.read(7);
  e_pass+= (char)EEPROM.read(8);
  e_pass+= (char)EEPROM.read(9);
  e_pass+= (char)EEPROM.read(10);
  e_pass+= (char)EEPROM.read(11);
  e_pass+= (char)EEPROM.read(12);
  e_pass+= (char)EEPROM.read(13);
  e_pass+= (char)EEPROM.read(14);
  e_pass+= (char)EEPROM.read(15);   
  return e_pass;
}

String GET_SSID(){
  String e_ssid;
  e_ssid= (char)EEPROM.read(17);
  e_ssid+= (char)EEPROM.read(18);
  e_ssid+= (char)EEPROM.read(19);
  e_ssid+= (char)EEPROM.read(20);
  e_ssid+= (char)EEPROM.read(21);
  e_ssid+= (char)EEPROM.read(22);
  e_ssid+= (char)EEPROM.read(23);
  e_ssid+= (char)EEPROM.read(24);
  e_ssid+= (char)EEPROM.read(25);
  e_ssid+= (char)EEPROM.read(26);
  e_ssid+= (char)EEPROM.read(27);
  e_ssid+= (char)EEPROM.read(28);
  e_ssid+= (char)EEPROM.read(29);
  e_ssid+= (char)EEPROM.read(30);
  e_ssid+= (char)EEPROM.read(31);
  e_ssid+= (char)EEPROM.read(32);  
  return e_ssid;
}

void SET_PASS(String e_pass){
 for (int i=0;i<=16;i++){EEPROM.write(i,e_pass.charAt(i)); EEPROM.commit();}
  
}

void SET_SSID(String e_ssid){
 for (int i=17;i<=32;i++){EEPROM.write(i,e_ssid.charAt(i-17)); EEPROM.commit();}
  
}





