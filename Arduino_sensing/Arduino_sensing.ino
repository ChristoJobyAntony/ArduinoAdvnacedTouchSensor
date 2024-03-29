   

   
   //****************************************************************************************
// Illutron take on Disney style capacitive touch sensor using only passives and Arduino
// Dzl 2012
//****************************************************************************************


//                              10n
// PIN 9 --[10k]-+-----10mH---+--||-- OBJECT
//               |            |
//              3.3k          |
//               |            V 1N4148 diode
//              GND           |
//                            |
//Analog 0 ---+------+--------+
//            |      |
//          100pf   1MOmhm
//            |      |
//           GND    GND



#define SET(x,y) (x |=(1<<y))				//-Bit set/clear macros
#define CLR(x,y) (x &= (~(1<<y)))       		// |
#define CHK(x,y) (x & (1<<y))           		// |
#define TOG(x,y) (x^=(1<<y))            		//-+



#define N 160  //How many frequencies

float results[N];            //-Filtered result buffer
float freq[N];            //-Filtered result buffer
int sizeOfArray = N;

 
   
   

void setup()
{
  
//  Timer/Counter1 Control Register A
//  Bit7:6 10 -> Clear OC1A/OC1B on compare match, set OC1A/OC1B 
//  Bit5:4 00 -> OC1B is disconnected
//  Bit1:0 10 -> Wave form Gerneation mdoe 
  TCCR1A=0b10000010;        //-Set up frequency generator

// Timer/Counter1 Control Register B
// Bit2:0 Clock Select: (001) CLK 1 i/o no prescaling
// Bit4:3 Waveform generation mode(11) (1110) : Fast PWM
  TCCR1B=0b00011001;        //-+
// The input capture is updated with the counter (TCNT1) value each time an event occurs on the ICP1 pin (or optionally on the 
// analog comparator output for Timer/Counter1). The input capture can be used for defining the counter TOP value
  ICR1=110;
// Output Compare register 1
  OCR1A=55;

  pinMode(9,OUTPUT);        //-Signal generator pin
  pinMode(8,OUTPUT);        //-Sync (test) pin

  Serial.begin(115200);

  for(int i=0;i<N;i++)      //-Preset results
    results[i]=0;         //-+
}

void loop()
{
  unsigned int d;

  int counter = 0;
  for(unsigned int d=0;d<N;d++)
  {
    int v=analogRead(0);    //-Read response signal
    CLR(TCCR1B,0);          //-Stop generator
    TCNT1=0;                //-Reload new frequency
    ICR1=d;                 // |
    OCR1A=d/2;              //-+
    SET(TCCR1B,0);          //-Restart generator

    results[d]=results[d]*0.5+(float)(v)*0.5; //Filter results
   
    freq[d] = d;

//    plot(v,0);              //-Display
//    plot(results[d],1);
   delayMicroseconds(1);
  }


  PlottArray(1,freq,results); 
  TOG(PORTB,0);            //-Toggle pin 8 after each sweep (good for scope)
}
   

   
    
 
