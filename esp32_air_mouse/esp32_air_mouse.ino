#include <Arduino.h>
#include <Wire.h>
#include "I2Cdev.h"
#include "MPU6050_6Axis_MotionApps20.h"
#include <WiFi.h>

// AP mode credentials
const char* ap_ssid = "ESP32-AirMouse";
const char* ap_password = "password";

// Create a WiFi server on port 80
WiFiServer server(80);
WiFiClient client;

MPU6050 mpu;
int16_t ax, ay, az, gx, gy, gz;
int vx, vy;
int gx_offset = 0;
int gz_offset = 0;
bool isCalibrating = false;
bool isInitialized = false;
bool isFirstConnect = true;
bool isGestureMode = false;
bool clientConnected = false;

Quaternion q;           // quaternion container
VectorFloat gravity;    // gravity vector
float ypr[3];           // yaw/pitch/roll container
uint16_t packetSize = 42;    // expected DMP packet size
uint16_t fifoCount;     // count of all bytes currently in FIFO
uint8_t fifoBuffer[64]; // FIFO storage buffer
uint8_t mpuIntStatus;   // holds actual interrupt status byte from MPU
float yaw = 0.0, pitch = 0.0, roll = 0.0;
float vertZero = 0, horzZero = 0;
float vertValue, horzValue;
float prev_vx = 0, prev_vy = 0;

// Cursor control constants
const float MOUSE_SPEED = 5.0;         // Multiplier for cursor movement
const float TILT_THRESHOLD = 10.0;     // Minimum tilt angle to start movement
const float MAX_TILT = 45.0;           // Tilt angle for maximum speed
const float BASE_SPEED = 2.0;          // Base cursor speed
const float MAX_SPEED = 15.0;          // Maximum cursor speed
const float DEADZONE = 2.0;            // Deadzone to prevent drift
const float SMOOTHING_FACTOR = 0.8;    // Higher = more smoothing (0.0-1.0)

// Gesture thresholds (from Arduino example)
const int THRESHOLD_LOW = 80;
const int THRESHOLD_HIGH = 145;
const int NEUTRAL_LOW = 100;
const int NEUTRAL_HIGH = 170;

// Calibration settings
const int CALIBRATION_SAMPLES = 100;
const int SAMPLE_DELAY = 10;
const int MOVEMENT_THRESHOLD = 1000;

float pitch_offset = 0;
float roll_offset = 0;
bool tilt_calibrated = false;

// Pin definitions
const int SDA_PIN = 21;
const int SCL_PIN = 22;

// Last gesture tracking
unsigned long lastGestureTime = 0;
const unsigned long GESTURE_COOLDOWN = 500;

// Helper function for sign
float sign(float value) {
    if (value > 0) return 1.0;
    if (value < 0) return -1.0;
    return 0.0;
}

void setup() {
    Serial.begin(115200);
    delay(1000);
    
    // Start Access Point
    WiFi.softAP(ap_ssid, ap_password);
    Serial.println("Access Point started");
    Serial.print("IP Address: ");
    Serial.println(WiFi.softAPIP());  // Usually 192.168.4.1
    
    // Start the server
    server.begin();
    Serial.println("Server started");
    
    Wire.begin(SDA_PIN, SCL_PIN);
    Serial.println("Initializing MPU6050...");
    
    mpu.initialize();
    mpu.dmpInitialize();

    // These offsets may need to be calibrated for your specific sensor
    mpu.setXGyroOffset(220);
    mpu.setYGyroOffset(76);
    mpu.setZGyroOffset(-85);
    mpu.setZAccelOffset(1788);
    
    mpu.setDMPEnabled(true);
    
    if (!mpu.testConnection()) {
        Serial.println("MPU6050 connection failed!");
        while (1) {
            delay(1000);
        }
    }
    
    mpu.setFullScaleGyroRange(MPU6050_GYRO_FS_1000);
    mpu.setDLPFMode(MPU6050_DLPF_BW_20);
    
    Serial.println("MPU6050 connection successful!");
    
    isInitialized = true;
    isFirstConnect = true;
}

void loop() {
    // Check if a client has connected
    if (!clientConnected) {
        client = server.available();
        if (client) {
            Serial.println("New client connected");
            clientConnected = true;
            client.println("INIT_COMPLETE");
        }
    } else {
        // Check if client is still connected
        if (!client.connected()) {
            Serial.println("Client disconnected");
            clientConnected = false;
            return;
        }
        
        // Check for incoming commands
        if (client.available()) {
            String command = client.readStringUntil('\n');
            command.trim();
            
            if (command == "INIT_CHECK") {
                client.println("INIT_COMPLETE");
            }
            else if (command == "CALIBRATE") {
                calibrateSensor();
            }
            else if (command == "GESTURE_MODE") {
                isGestureMode = true;
                isCalibrating = false;
                client.println("MODE_GESTURE");
            }
            else if (command == "CURSOR_MODE") {
                isGestureMode = false;
                isCalibrating = false;
                client.println("MODE_CURSOR");
            }
            else if (command == "CALIBRATE_TILT") {
                calibrateTilt();
            }
            else if (command == "CENTER_CURSOR") {
                // This will be handled by Python to center the cursor
                client.println("CURSOR_CENTERED");
            }
        }

        // Send sensor data
        if (!isCalibrating && isInitialized) {
            if (isGestureMode) {
                handleGestureMode();
            } else {
                sendMotionData();
            }
        }
    }
    
    delay(20);  // 50Hz update rate
}

void handleGestureMode() {
    // Get motion data
    mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);
    
    // Map acceleration values exactly like the Arduino example
    byte mappedX = map(ax, -17000, 17000, 0, 255);
    byte mappedY = map(ay, -17000, 17000, 0, 255);
    
    // Debug output (optional)
    if (clientConnected) {
        client.print("DEBUG,X=");
        client.print(mappedX);
        client.print(",Y=");
        client.println(mappedY);
    }
    
    // Apply cooldown to prevent rapid gesture triggers
    unsigned long currentTime = millis();
    if (currentTime - lastGestureTime < GESTURE_COOLDOWN) {
        return;
    }
    
    // Check for gestures using the same logic as the Arduino example
    if (mappedY < THRESHOLD_LOW) {
        if (clientConnected) client.println("GESTURE,DOWN");  // gesture 1
        lastGestureTime = currentTime;
    }
    else if (mappedY > THRESHOLD_HIGH) {
        if (clientConnected) client.println("GESTURE,UP");  // gesture 2
        lastGestureTime = currentTime;
    }
    else if (mappedX > THRESHOLD_HIGH) {
        if (clientConnected) client.println("GESTURE,LEFT");  // gesture 3
        lastGestureTime = currentTime;
    }
    else if (mappedX < THRESHOLD_LOW) {
        if (clientConnected) client.println("GESTURE,RIGHT");  // gesture 4
        lastGestureTime = currentTime;
    }
    else if (mappedX > NEUTRAL_LOW && mappedX < NEUTRAL_HIGH && 
             mappedY > THRESHOLD_LOW && mappedY < 130) {
        if (clientConnected) client.println("GESTURE,SLIGHT_DOWN");  // gesture 5
        lastGestureTime = currentTime;
    }
}

void calibrateSensor() {
    if (clientConnected) client.println("CALIBRATION_START");
    isCalibrating = true;
    
    long gx_sum = 0;
    long gz_sum = 0;
    int valid_samples = 0;
    
    for(int i = 0; i < CALIBRATION_SAMPLES; i++) {
        mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);
        
        if (abs(gx) < MOVEMENT_THRESHOLD && abs(gz) < MOVEMENT_THRESHOLD) {
            gx_sum += gx;
            gz_sum += gz;
            valid_samples++;
        }
        
        int progress = ((i + 1) * 100) / CALIBRATION_SAMPLES;
        if (clientConnected) {
            client.print("CALIBRATION_PROGRESS,");
            client.println(progress);
        }
        
        delay(SAMPLE_DELAY);
    }
    
    if (valid_samples > 0) {
        gx_offset = gx_sum / valid_samples;
        gz_offset = gz_sum / valid_samples;
    }
    
    isCalibrating = false;
    if (clientConnected) client.println("CALIBRATION_COMPLETE");
}

void calibrateTilt() {
    if (clientConnected) client.println("TILT_CALIBRATION_START");
    isCalibrating = true;
    
    // Variables for averaging
    float pitch_sum = 0;
    float roll_sum = 0;
    
    // Collect samples
    for(int i = 0; i < CALIBRATION_SAMPLES; i++) {
        mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);
        
        // Calculate tilt angles
        float accel_x = ax;
        float accel_y = ay;
        float accel_z = az;
        
        float pitch = atan2(accel_y, sqrt(accel_x * accel_x + accel_z * accel_z)) * 180.0 / PI;
        float roll = atan2(-accel_x, accel_z) * 180.0 / PI;
        
        pitch_sum += pitch;
        roll_sum += roll;
        
        // Send progress
        int progress = ((i + 1) * 100) / CALIBRATION_SAMPLES;
        if (clientConnected) {
            client.print("CALIBRATION_PROGRESS,");
            client.println(progress);
        }
        
        delay(SAMPLE_DELAY);
    }
    
    // Calculate offsets
    pitch_offset = pitch_sum / CALIBRATION_SAMPLES;
    roll_offset = roll_sum / CALIBRATION_SAMPLES;
    tilt_calibrated = true;
    
    isCalibrating = false;
    if (clientConnected) {
        client.println("TILT_CALIBRATION_COMPLETE");
        client.print("Pitch offset: ");
        client.print(pitch_offset);
        client.print(", Roll offset: ");
        client.println(roll_offset);
    }
}

void sendMotionData() {
    mpuIntStatus = mpu.getIntStatus();
    fifoCount = mpu.getFIFOCount();
    
    if ((mpuIntStatus & 0x10) || fifoCount == 1024) {
        // FIFO overflow - reset
        mpu.resetFIFO();
    } else if (mpuIntStatus & 0x02) {
        // Wait for correct data length
        while (fifoCount < packetSize) {
            fifoCount = mpu.getFIFOCount();
        }
        
        // Read packet from FIFO
        mpu.getFIFOBytes(fifoBuffer, packetSize);
        
        // Get Quaternion, Gravity, and YPR
        mpu.dmpGetQuaternion(&q, fifoBuffer);
        mpu.dmpGetGravity(&gravity, &q);
        mpu.dmpGetYawPitchRoll(ypr, &q, &gravity);
        
        // Convert to degrees
        yaw = ypr[0] * 180/M_PI;
        pitch = ypr[1] * 180/M_PI;
        roll = ypr[2] * 180/M_PI;
        
        // Calculate relative movement
        vertValue = pitch - vertZero;
        horzValue = roll - horzZero;
        
        // Update previous values
        vertZero = pitch;
        horzZero = roll;
        
        // Apply deadzone to filter out small movements
        if (abs(horzValue) < DEADZONE) horzValue = 0;
        if (abs(vertValue) < DEADZONE) vertValue = 0;
        
        // Apply adaptive sensitivity - faster movements get higher sensitivity
        float sensitivity = BASE_SPEED;
        if (abs(horzValue) > 5.0) sensitivity *= 1.5;
        if (abs(horzValue) > 10.0) sensitivity *= 2.0;
        
        if (abs(vertValue) > 5.0) sensitivity *= 1.5;
        if (abs(vertValue) > 10.0) sensitivity *= 2.0;
        
        // Calculate raw cursor velocity with non-linear response
        float raw_vx = sign(horzValue) * pow(abs(horzValue), 1.5) * sensitivity;
        float raw_vy = sign(vertValue) * pow(abs(vertValue), 1.5) * sensitivity;
        
        // Apply smoothing
        float vx = (raw_vx * (1.0 - SMOOTHING_FACTOR)) + (prev_vx * SMOOTHING_FACTOR);
        float vy = (raw_vy * (1.0 - SMOOTHING_FACTOR)) + (prev_vy * SMOOTHING_FACTOR);
        
        // Store for next iteration
        prev_vx = vx;
        prev_vy = vy;
        
        // Limit maximum speed
        if (abs(vx) > MAX_SPEED) vx = (vx > 0) ? MAX_SPEED : -MAX_SPEED;
        if (abs(vy) > MAX_SPEED) vy = (vy > 0) ? MAX_SPEED : -MAX_SPEED;
        
        if (clientConnected) {
            client.print("CURSOR,");
            client.print(vx);
            client.print(",");
            client.println(vy);
        }
        
        // Debug output
        Serial.print("YPR: ");
        Serial.print(yaw);
        Serial.print(", ");
        Serial.print(pitch);
        Serial.print(", ");
        Serial.print(roll);
        Serial.print(" | Movement: ");
        Serial.print(vx);
        Serial.print(", ");
        Serial.println(vy);
    }
}