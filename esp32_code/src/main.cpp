#include <Arduino.h>
#include <Wire.h>
#include "I2Cdev.h"
#include "MPU6050_6Axis_MotionApps20.h"
#include <WiFi.h>

// WiFi Configuration
const char* ap_ssid = "ESP32";
const char* ap_password = "password";
WiFiServer server(80);
WiFiClient client;

void handleWiFiConnection();
void handleCursorMode();
void handleGestureMode();
void calibrateSensor();
bool detectCircleGesture(float cal_gx, float cal_gy, float cal_gz);
bool isValidMovement();
bool detectShakeGesture(float cal_gx);
bool isValidMovement();
bool isAtRest();
void checkDirectionalGestures(String* gesture);
void sendGesture(const String& gesture);
void calibrateSensors();
String detectTiltGesture();


// MPU6050 Configuration
MPU6050 mpu;
int16_t ax, ay, az, gx, gy, gz;
int gx_offset = 0, gy_offset = 0, gz_offset = 0;
float resting_accel = 0, resting_gyro = 0;
int tilt_direction = 0;              // -1=left, 0=neutral, 1=right
uint32_t last_tilt_time = 0;
int tilt_count = 0;
int tilt_threshold = 8000;           // Minimum gyro value for tilt detection


unsigned long lastGestureTime = 0;
const unsigned long GESTURE_COOLDOWN = 500; // 500ms cooldown
String lastGesture = "";
const int GESTURE_UP_THRESHOLD = 10000;
const int GESTURE_DOWN_THRESHOLD = -15000;
const int GESTURE_LEFT_THRESHOLD = 10000;
const int GESTURE_RIGHT_THRESHOLD = -10000;
const int GESTURE_SLIGHT_DOWN_THRESHOLD = -5000;

// Gesture Detection Constants
#define CIRCLE_THRESHOLD 8000     // Minimum angular velocity (deg/s)
#define GESTURE_WINDOW_MS 2000    // Max time to complete gesture
#define CIRCLE_MIN_VELOCITY 10000   // Increased from 8000 (raw gyro value)
#define CIRCLE_MIN_ROTATION 540     // Require 1.5 full rotations (540°)
#define CIRCLE_MAX_TIME 1500        // Must complete within 1.5 seconds
#define RESTING_THRESHOLD 3000      // Max acceleration when stationary
#define CIRCLE_MIN_CONSECUTIVE_SAMPLES 10  // Must maintain threshold
#define CIRCLE_ANGLE_THRESHOLD 5000        // Minimum angular velocity
#define GESTURE_COOLDOWN_MS 300        
#define CIRCLE_PURITY_THRESHOLD 3000 // Max allowed tilt during circle
#define SPEED_FACTOR 0.02

// Shake detection variables
const int SHAKE_TILT_THRESHOLD = 12000; // Adjust as needed
const int SHAKE_MIN_ALTERNATIONS = 2;   // Number of left/right alternations
const int SHAKE_WINDOW_MS = 2000;        // Time window for shake (ms)
int shake_state = 0;                    // 0: neutral, 1: right, -1: left
int shake_count = 0;
unsigned long shake_start_time = 0;

// Operation Modes
enum Mode { IDLE, CURSOR, GESTURE };
Mode currentMode = IDLE;

void setup() {
    Serial.begin(115200);
    Wire.begin();
    
    // Initialize MPU6050
    mpu.initialize();
    if (!mpu.testConnection()) {
      Serial.println("MPU6050 connection failed!");
      while(1);
    }
    
    // Start WiFi AP
    WiFi.softAP(ap_ssid, ap_password);
    server.begin();
    Serial.println("FlowTech GestureKit Ready");
    
    // Calibrate sensors
    calibrateSensors();
}

void loop() {
    handleWiFiConnection();
    mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);
    
    switch(currentMode) {
        case CURSOR:
            handleCursorMode();
            break;
        case GESTURE:
            handleGestureMode();
            break;
        default:
            delay(10);
    }
}

bool detectCircleGesture(float cal_gx, float cal_gy, float cal_gz) {
    // Only detect circle if tilt is minimal and rotation (gz) is high
    const int CIRCLE_GZ_THRESHOLD = 12000; // adjust as needed
    const int TILT_TOLERANCE = 3000;       // max allowed tilt during circle

    if (abs(cal_gx) < TILT_TOLERANCE && abs(cal_gy) < TILT_TOLERANCE && abs(cal_gz) > CIRCLE_GZ_THRESHOLD) {
        static unsigned long lastCircleTime = 0;
        if (millis() - lastCircleTime > 1000) { // 1s cooldown
            lastCircleTime = millis();
            return true;
        }
    }
    return false;
}

bool detectShakeGesture(float cal_gx) {
    // Detect rapid left/right alternations
    static int last_state = 0;
    static int alternations = 0;
    static unsigned long window_start = 0;

    int current_state = 0;
    if (cal_gx > SHAKE_TILT_THRESHOLD) current_state = 1;
    else if (cal_gx < -SHAKE_TILT_THRESHOLD) current_state = -1;

    if (current_state != 0 && current_state != last_state) {
        if (alternations == 0) window_start = millis();
        alternations++;
        last_state = current_state;
    }

    // Reset if too slow
    if (alternations > 0 && millis() - window_start > SHAKE_WINDOW_MS) {
        alternations = 0;
        last_state = 0;
    }

    // Shake detected
    if (alternations >= SHAKE_MIN_ALTERNATIONS) {
        alternations = 0;
        last_state = 0;
        return true;
    }
    return false;
}

bool isValidMovement() {
    // Require minimum acceleration to prevent false positives
    float accel_magnitude = sqrt(ax*ax + ay*ay + az*az);
    return (accel_magnitude > 5000); // Adjust this threshold as needed
}

void handleWiFiConnection() {
    if (!client || !client.connected()) {
        client = server.available();
        return;
    }
    
    if (client.available()) {
        String command = client.readStringUntil('\n');
        command.trim();
        
        if (command == "CURSOR_MODE") {
            currentMode = CURSOR;
            client.println("MODE_CURSOR");
        } 
        else if (command == "GESTURE_MODE") {
            currentMode = GESTURE;
            client.println("MODE_GESTURE");
        }
        else if (command == "CALIBRATE") {
            calibrateSensors();
        }
    }
}

void handleCursorMode() {
    // Apply calibration and scaling
    float vx = (gz - gz_offset) * -SPEED_FACTOR;
    float vy = (gx - gx_offset) * -SPEED_FACTOR;
    if (client.connected()) {
        client.print("CURSOR,");
        client.print(vx);
        client.print(",");
        client.println(vy);
    }
    delay(20);
}

void handleGestureMode() {
    mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);

    // Apply calibration offsets
    float cal_gx = gx - gx_offset;
    float cal_gy = gy - gy_offset;
    float cal_gz = gz - gz_offset;

    if (millis() - lastGestureTime < GESTURE_COOLDOWN) {
        return;
    }

    // Detect gestures
    String currentGesture = "";
    // Check for circle gesture first (in-plane, no tilt)
    if (detectCircleGesture(cal_gx, cal_gy, cal_gz)) {
        currentGesture = "CIRCLE";
    }
    // Check for shake gesture (rapid left/right alternation)
    else if (detectShakeGesture(cal_gx)) {
        currentGesture = "SHAKE";
        // Switch to cursor mode on shake
        currentMode = CURSOR;
        if (client) client.println("MODE_CURSOR");
    }
    // Only check for tilt gestures if not doing a circle
    else if (cal_gy > GESTURE_UP_THRESHOLD) {
        currentGesture = "DOWN";
    } 
    else if (cal_gy < GESTURE_DOWN_THRESHOLD || cal_gy < GESTURE_SLIGHT_DOWN_THRESHOLD) {
        currentGesture = "UP";
    }
    else if (cal_gx > GESTURE_LEFT_THRESHOLD) {
        currentGesture = "RIGHT";
    }
    else if (cal_gx < GESTURE_RIGHT_THRESHOLD) {
        currentGesture = "LEFT";
    }

    if (currentGesture != "" && currentGesture != lastGesture) {
        if (client) {
            client.print("GESTURE_DETECTED,");
            client.println(currentGesture);
            sendGesture(currentGesture);
        }
        lastGesture = currentGesture;
        lastGestureTime = millis();
    }
    
    // Reset lastGesture if we're back to neutral
    if (abs(cal_gx) < (GESTURE_LEFT_THRESHOLD/2) && 
        abs(cal_gy) < (GESTURE_UP_THRESHOLD/2) &&
        abs(cal_gz) < 3000) {
        lastGesture = "";
    }
}

// Helper functions
bool isAtRest() {
    float accel = sqrt(ax*ax + ay*ay + az*az);
    float gyro = sqrt(gx*gx + gy*gy + gz*gz);
    return (accel < 1000 && gyro < 100); // Customize thresholds
}

void sendGesture(const String& gesture) {
    if (client.connected()) {
      client.print("GESTURE,");
      client.println(gesture);
      client.flush();
    }
    Serial.println("Sent gesture: " + gesture);
  }

void checkDirectionalGestures(String* gesture) {
    // Your existing directional detection
    if (gy > 10000) *gesture = "UP";
    else if (gy < -10000) *gesture = "DOWN";
    else if (gx > 10000) *gesture = "LEFT";
    else if (gx < -10000) *gesture = "RIGHT";
}

void calibrateSensors() {
    // Calibrate gyro offsets
    long gx_sum = 0, gy_sum = 0, gz_sum = 0;
    long accel_sum = 0, gyro_sum = 0;
    
    for(int i=0; i<100; i++) {
      mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);
      gx_sum += gx;
      gy_sum += gy;
      gz_sum += gz;
      accel_sum += sqrt(ax*ax + ay*ay + az*az);
      gyro_sum += sqrt(gx*gx + gy*gy + gz*gz);
      delay(10);
    }
    
    gx_offset = gx_sum / 100;
    gy_offset = gy_sum / 100;
    gz_offset = gz_sum / 100;
    resting_accel = accel_sum / 100;
    resting_gyro = gyro_sum / 100;

    Serial.println("Keep sensor level for tilt calibration...");
    delay(3000);
    for(int i=0; i<100; i++) {
        mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);
        gx_sum += gx;
        delay(10);
    }
    tilt_threshold = abs(gx_sum / 100) * 1.5; // Dynamic threshold
    Serial.println("Calibration complete");
  }