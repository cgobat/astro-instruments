const int SHUTTER_PIN = 2; // pin for shutter switch
int shutterState; // current switch state
int prevState = HIGH; // previous switch state
bool clockSet = false; // has clock ever been set?
float startTime; // exposure start time
const char *states[] = {"closed","open"};

void setup()
{
  pinMode(13, OUTPUT); // LED
  pinMode(SHUTTER_PIN, INPUT_PULLUP);
  Serial.begin(9600);
  Serial.flush();
}

void loop()
{
  shutterState = digitalRead(SHUTTER_PIN);
  if (shutterState != prevState) {
    if (clockSet == false) { // if the button has never been pressed before
      startTime = millis()/1000.0; // reset the working clock
      clockSet = true;
    }
    digitalWrite(13,1-shutterState);
    Serial.print("At time ");
    Serial.print(millis()/1000.0 - startTime);
    Serial.print(", switch changed from ");
    Serial.print(states[prevState]);
    Serial.print(" to ");
    Serial.print(states[shutterState]);
    Serial.println();
    prevState = shutterState;
  }
}
