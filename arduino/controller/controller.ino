//  photobooth arduino control
//
//  pin 2:   switch to start photo session
//  pin 3:   unused switch
//  pin 4-7: relay
//  pin 10:  servo
//
//  protocol: command/argument
//
//  outgoing => to host:
//  0x00: reserved
//  0x01: switch trigger [value: pin number]
//
//  incoming => from host:
//  0x80: set tilt [value: 0-180 ]
//  0x81: engage relay [0-3]
//  0x82: disengage relay [0-3]
//
//  All relays are turned off when arduino is started
//
// This file is copyright Leif Theden 2012-2015.
// GPL v3

#include <Servo.h>

// protocol declarations
// 'p' prefix signifies 'protocol'
byte pSwitchTrigger = 0x01;
byte pSetTilt       = 0x80;
byte pRelayOn       = 0x81;
byte pRelayOff      = 0x82;

// pin configuration
int tiltServoPin = 10;
int ledPin = 13;

// relay mapping
unsigned char relayMapping[4] = {4,5,6,7};

// define our servo and the physical limits of it
Servo tiltServo;
int tiltPosNegativeLimit = 20;
int tiltPosPositiveLimit = 160;
int tiltPos = tiltPosNegativeLimit;
int servoResetFreq = 50;
long lastServoResetTime = 0;

// incoming protocol buffer
byte serBufferData[2];
byte serBufferIndex = 0;

// debounce on switch pins
int triggerState[] = {HIGH, HIGH};
int triggerHeld[]  = {0, 0};
int lastTriggerState[]  = {HIGH, HIGH};
long lastDebounceTime[] = {0, 0};
long debounceDelay = 100;

void setup() {
  // start communication with pc
  Serial.begin(56700);

  // switches
  pinMode(2, INPUT_PULLUP);
  pinMode(3, INPUT_PULLUP);

  // relays
  pinMode(4, OUTPUT);
  pinMode(5, OUTPUT);
  pinMode(6, OUTPUT);
  pinMode(7, OUTPUT);

  // led
  pinMode(ledPin, OUTPUT);

  // servo
  tiltServo.attach(tiltServoPin);
}

void readPin(int pin) {
  int thisState = digitalRead(pin);
  long now = millis();

  // subtract 2 b/c our inputs begin at 2 --
  // pins 0 and 1 are reserved for serial communication
  int index = pin;
  index -= 2;

  if (thisState != lastTriggerState[index]) {
    lastDebounceTime[index] = now;
  }

  if ((now - lastDebounceTime[index]) > debounceDelay) {
    triggerState[index] = thisState;
  }

  if (triggerState[index] == LOW) {
    if (triggerHeld[index] == 0) {
      triggerHeld[index] = 1;
      Serial.write(pSwitchTrigger);
      Serial.write(pin);
      Serial.flush();
    }
  }
  else {
    triggerHeld[index] = 0;
  }

  lastTriggerState[index] = thisState;
}

void setTilt(byte newValue) {
  int value = (int)newValue;

  if (value > tiltPosPositiveLimit) {
    value = tiltPosPositiveLimit;
  }
  if (value < tiltPosNegativeLimit) {
    value = tiltPosNegativeLimit;
  }

  if (tiltPosPositiveLimit >= value) {
    if (tiltPosNegativeLimit <= value) {
      tiltPos = value;
    }
  }
}

// Arduino Loop.  Not all functions are handled here
void loop() {
  readPin(2);
  readPin(3);

  long now = millis();
  if ((now - lastServoResetTime) > servoResetFreq) {
    lastServoResetTime = now;
    tiltServo.write(tiltPos);
  }
}

// Handle incoming serial data (not directly tied to loop())
void serialEvent() {
  byte cmd;

  while (Serial.available()) {
    serBufferData[serBufferIndex] = (byte)Serial.read();
    cmd = serBufferData[0];

    if (serBufferIndex == 1) {
      serBufferIndex = 0;
    } else {
      serBufferIndex += 1;
    }

    if (serBufferIndex == 0) {
      byte arg = serBufferData[1];

      if (cmd == pSetTilt) {
        setTilt(arg);
      }

      if (cmd == pRelayOn) {
        int pin = (int)arg;
        pin -= 1;
        digitalWrite(relayMapping[pin], HIGH);
      }

      if (cmd == pRelayOff) {
        int pin = (int)arg;
        pin -= 1;
        digitalWrite(relayMapping[pin], LOW);
      }

      break;
    }
  }
}
