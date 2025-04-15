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
bool detectCircle();
bool isValidMovement();
bool detectShake();
bool isValidMovement();
bool isAtRest();
void checkDirectionalGestures(String* gesture);
void sendGesture(const String& gesture);
void calibrateSensors();


// MPU6050 Configuration
MPU6050 mpu;
int16_t ax, ay, az, gx, gy, gz;
int gx_offset = 0, gy_offset = 0, gz_offset = 0;
float resting_accel = 0, resting_gyro = 0;

// Gesture Detection Constants
#define CIRCLE_THRESHOLD 8000     // Minimum angular velocity (deg/s)
#define SHAKE_THRESHOLD 20000     // Minimum acceleration (raw values)
#define GESTURE_WINDOW_MS 2000    // Max time to complete gesture
#define SHAKE_COUNT 3             // Required number of shakes
#define CIRCLE_MIN_VELOCITY 10000   // Increased from 8000 (raw gyro value)
#define CIRCLE_MIN_ROTATION 540     // Require 1.5 full rotations (540°)
#define CIRCLE_MAX_TIME 1500        // Must complete within 1.5 seconds
#define SHAKE_MIN_ACCEL 18000       // Minimum acceleration to count as shake
#define SHAKE_COOLDOWN_MS 300       // Time between shake counts
#define SHAKES_REQUIRED 3           // Number of shakes needed
#define SHAKE_WINDOW_MS 1000        // Time window to complete all shakes
#define RESTING_THRESHOLD 3000      // Max acceleration when stationary
#define SHAKE_DEBOUNCE_MS 500       // Minimum time between shake events
#define CIRCLE_MIN_CONSECUTIVE_SAMPLES 10  // Must maintain threshold
#define CIRCLE_ANGLE_THRESHOLD 5000        // Minimum angular velocity
#define GESTURE_COOLDOWN_MS 300

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

bool detectCircle() {
    static uint8_t valid_samples = 0;
    static bool circle_detected = false;
    float gyro_mag = sqrt(gx*gx + gy*gy);
    
    // 1. Check angular velocity threshold
    if (gyro_mag > CIRCLE_ANGLE_THRESHOLD) {
        valid_samples++;
        
        // 2. Require sustained motion
        if (valid_samples >= CIRCLE_MIN_CONSECUTIVE_SAMPLES && !circle_detected) {
            circle_detected = true;
            return true;
        }
    } else {
        valid_samples = 0;
        circle_detected = false;
    }
    return false;
}

bool detectShake() {
    static uint32_t last_valid_shake = 0;
    float accel_mag = sqrt(ax*ax + ay*ay + az*az);
    
    // 1. Reject if device is at rest
    if (accel_mag < RESTING_THRESHOLD) return false;
    
    // 2. Apply time-based debouncing
    if (millis() - last_valid_shake < SHAKE_DEBOUNCE_MS) return false;
    
    // 3. Require sudden acceleration changes
    static float last_mag = 0;
    float delta = abs(accel_mag - last_mag);
    last_mag = accel_mag;
    
    if (delta > SHAKE_MIN_ACCEL) {
        last_valid_shake = millis();
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
    float vx = (gx - gx_offset) / 150.0;
    float vy = (gy - gy_offset) / 150.0;
    
    if (client.connected()) {
        client.print("CURSOR,");
        client.print(vx);
        client.print(",");
        client.println(vy);
    }
    delay(20);
}

void handleGestureMode() {
    static uint32_t last_gesture_time = 0;
    const uint32_t GESTURE_COOLDOWN = 300; // ms
    
    // Cooldown period
    if (millis() - last_gesture_time < GESTURE_COOLDOWN) return;
    
    String detected_gesture = "";
    
    // 1. Check for stationary state first
    if (isAtRest()) {
        return; // Skip processing when idle
    }
    
    // 2. Implement detection hierarchy
    if (detectShake()) {
        detected_gesture = "SHAKE";
    } 
    else if (detectCircle()) {
        detected_gesture = "CIRCLE";
    }
    else {
        // Only check directions if no complex gesture
        checkDirectionalGestures(&detected_gesture);
    }
    
    if (detected_gesture != "") {
        last_gesture_time = millis();
        sendGesture(detected_gesture);
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
    
    Serial.println("Calibration complete");
  }