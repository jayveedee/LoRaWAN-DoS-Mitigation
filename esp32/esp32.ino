#include <RadioLib.h>

#define LORA_SCK        05
#define LORA_MISO       19
#define LORA_MOSI       27
#define LORA_SS         18
#define LORA_DIO0       26
#define LORA_DIO1       33
#define LORA_RST        14

float frequency =       867.1;

SX1276 radio = new Module(LORA_SS, LORA_DIO0, LORA_RST, LORA_DIO1);

void setup() 
{

}

void loop() 
{

}
