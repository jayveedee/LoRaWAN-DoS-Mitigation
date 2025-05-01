#ifndef LDN_H_
#define LDN_H_

#include <Arduino.h>

#include "lib/Sodaq_RN2483/Sodaq_RN2483_internal.h"
#include "lib/Sodaq_RN2483/Sodaq_RN2483.h"
#include "lib/Sodaq_RN2483/Sodaq_RN2483.cpp"
#include "lib/Sodaq_RN2483/Utils.h"

class LDN {
    public:
        LDN();
        
        void setup();

}