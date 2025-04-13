#include <Arduino.h>
#include <Wire.h>
#include "I2Cdev.h"
#include "MPU6050_6Axis_MotionApps20.h"
#include <WiFi.h>

void calibrateSensor();
void calibrateTilt();
void handleGestureMode();
void handleCursorMode();
void sendCursorData(float vx, float vy);
float calculateTiltX(int16_t ax, int16_t ay, int16_t az);
float calculateTiltZ(int16_t ax, int16_t ay, int16_t az);

// AP mode credentials
const char *ap_ssid = "ESP32";
const char *ap_password = "password";

// Create a WiFi server on port 80
WiFiServer server(80);
WiFiClient client;

MPU6050 mpu;

// Raw sensor readings
int16_t ax, ay, az, gx, gy, gz;

// Calibration offsets
int gx_offset = 0, gy_offset = 0, gz_offset = 0;
float tilt_x_zero = 0.0, tilt_z_zero = 0.0;

// Operation flags
bool isCalibrating = false;
bool isInitialized = false;
bool isGestureMode = false;
bool clientConnected = false;

// DMP variables
Quaternion q;
VectorFloat gravity;
float ypr[3];
uint16_t packetSize = 42;
uint8_t fifoBuffer[64];

// Gesture detection thresholds
const int GESTURE_UP_THRESHOLD = 10000;
const int GESTURE_DOWN_THRESHOLD = -15000;
const int GESTURE_LEFT_THRESHOLD = 10000;
const int GESTURE_RIGHT_THRESHOLD = -10000;
const int GESTURE_SLIGHT_DOWN_THRESHOLD = -5000;

// Calibration settings
const int CALIBRATION_SAMPLES = 100;
const int SAMPLE_DELAY = 10;
const int MOVEMENT_THRESHOLD = 1000;

unsigned long lastGestureTime = 0;
const unsigned long GESTURE_COOLDOWN = 500; // 500ms cooldown
String lastGesture = "";

// Pin definitions
const int SDA_PIN = 21;
const int SCL_PIN = 22;

void setup() {
    // Initialize Serial first for debugging
    Serial.begin(115200);
    delay(1000);
    
    // Initialize WiFi
    WiFi.softAP(ap_ssid, ap_password);
    WiFi.softAPConfig(IPAddress(192,168,4,1), IPAddress(192,168,4,1), IPAddress(255,255,255,0));
    server.begin();
    
    // Initialize MPU6050
    Wire.begin(21, 22); // SDA, SCL
    mpu.initialize();
    
    if (!mpu.testConnection()) {
        Serial.println("MPU6050 connection failed!");
        while(1);
    }
    
    mpu.setFullScaleGyroRange(MPU6050_GYRO_FS_1000);
    mpu.setDLPFMode(MPU6050_DLPF_BW_20);
    isInitialized = true;
    
    Serial.println("System initialized");
  }

void loop()
{
    // Handle client connections
    if (!clientConnected)
    {
        client = server.available();
        if (client)
        {
            Serial.println("New client connected");
            clientConnected = true;
            client.println("INIT_COMPLETE");
        }
    }
    else
    {
        // Check if client is still connected
        if (!client.connected())
        {
            Serial.println("Client disconnected");
            clientConnected = false;
            return;
        }

        // Process incoming commands
        if (client.available())
        {
            String command = client.readStringUntil('\n');
            command.trim();

            if (command == "INIT_CHECK")
            {
                client.println("INIT_COMPLETE");
            }
            else if (command == "CALIBRATE")
            {
                calibrateSensor();
            }
            else if (command == "GESTURE_MODE")
            {
                isGestureMode = true;
                client.println("MODE_GESTURE");
            }
            else if (command == "CURSOR_MODE")
            {
                isGestureMode = false;
                client.println("MODE_CURSOR");
            }
            else if (command == "CALIBRATE_TILT")
            {
                calibrateTilt();
            }
        }

        // Send sensor data based on mode
        if (!isCalibrating && isInitialized)
        {
            if (isGestureMode)
            {
                handleGestureMode();
            }
            else
            {
                handleCursorMode();
            }
        }
    }

    delay(20); // 50Hz update rate
}

void handleCursorMode()
{
    mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);

    // Apply calibration offsets
    float cal_gx = gx - gx_offset;
    float cal_gy = gy - gy_offset;
    float cal_gz = gz - gz_offset;

    // Calculate tilt angles (using calibrated values)
    float tilt_x = atan2(ay, az) * 180.0 / PI - tilt_x_zero;
    float tilt_z = atan2(ax, az) * 180.0 / PI - tilt_z_zero;

    // Calculate cursor movement (simplified example)
    float vx = constrain(tilt_z * 0.5, -10, 10);
    float vy = constrain(tilt_x * 0.5, -10, 10);

    // Send cursor data
    if (clientConnected)
    {
        client.print("CURSOR,");
        client.print(vx);
        client.print(",");
        client.println(vy);
    }
}

void handleGestureMode()
{
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
    if (cal_gy > GESTURE_UP_THRESHOLD) {
        currentGesture = "UP";
    } 
    else if (cal_gy < GESTURE_DOWN_THRESHOLD) {
        currentGesture = "DOWN";
    }
    else if (cal_gy < GESTURE_SLIGHT_DOWN_THRESHOLD) {
        // Only register SLIGHT_DOWN if not currently in DOWN state
        if (lastGesture != "DOWN") {
            currentGesture = "SLIGHT_DOWN";
        } 
    }
    else if (cal_gx > GESTURE_LEFT_THRESHOLD) {
        currentGesture = "LEFT";
    }
    else if (cal_gx < GESTURE_RIGHT_THRESHOLD) {
        currentGesture = "RIGHT";
    }

    if (currentGesture != "" && currentGesture != lastGesture) {
        if (clientConnected) {
            client.print("GESTURE_DETECTED,");
            client.println(currentGesture);
        }
        lastGesture = currentGesture;
        lastGestureTime = millis();
    }
    
    // Reset lastGesture if we're back to neutral
    if (abs(cal_gx) < (GESTURE_LEFT_THRESHOLD/2) && 
        abs(cal_gy) < (GESTURE_UP_THRESHOLD/2)) {
        lastGesture = "";
    }
}

void calibrateSensor()
{
    if (clientConnected)
        client.println("CALIBRATION_START");
    isCalibrating = true;

    long gx_sum = 0, gy_sum = 0, gz_sum = 0;
    int valid_samples = 0;

    for (int i = 0; i < CALIBRATION_SAMPLES; i++)
    {
        mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);

        // Only use stable samples
        if (abs(gx) < MOVEMENT_THRESHOLD &&
            abs(gy) < MOVEMENT_THRESHOLD &&
            abs(gz) < MOVEMENT_THRESHOLD)
        {
            gx_sum += gx;
            gy_sum += gy;
            gz_sum += gz;
            valid_samples++;
        }

        // Send progress
        if (clientConnected)
        {
            client.print("CALIBRATION_PROGRESS,");
            client.println((i * 100) / CALIBRATION_SAMPLES);
        }
        delay(SAMPLE_DELAY);
    }

    // Calculate new offsets
    if (valid_samples > 0)
    {
        gx_offset = gx_sum / valid_samples;
        gy_offset = gy_sum / valid_samples;
        gz_offset = gz_sum / valid_samples;
    }

    isCalibrating = false;
    if (clientConnected)
    {
        client.println("CALIBRATION_COMPLETE");
        client.print("Offsets - gx: ");
        client.print(gx_offset);
        client.print(", gy: ");
        client.print(gy_offset);
        client.print(", gz: ");
        client.println(gz_offset);
    }
}

void calibrateTilt()
{
    if (clientConnected)
        client.println("TILT_CALIBRATION_START");
    isCalibrating = true;

    float tilt_x_sum = 0, tilt_z_sum = 0;

    for (int i = 0; i < CALIBRATION_SAMPLES; i++)
    {
        mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);

        // Calculate current tilt
        tilt_x_sum += atan2(ay, az) * 180.0 / PI;
        tilt_z_sum += atan2(ax, az) * 180.0 / PI;

        // Send progress
        if (clientConnected)
        {
            client.print("TILT_CALIBRATION_PROGRESS,");
            client.println((i * 100) / CALIBRATION_SAMPLES);
        }
        delay(SAMPLE_DELAY);
    }

    // Calculate neutral tilt positions
    tilt_x_zero = tilt_x_sum / CALIBRATION_SAMPLES;
    tilt_z_zero = tilt_z_sum / CALIBRATION_SAMPLES;

    isCalibrating = false;
    if (clientConnected)
    {
        client.println("TILT_CALIBRATION_COMPLETE");
        client.print("Tilt zeros - X: ");
        client.print(tilt_x_zero);
        client.print(", Z: ");
        client.println(tilt_z_zero);
    }
}

void sendCursorData(float vx, float vy)
{
    if (clientConnected)
    {
        client.print("CURSOR,");
        client.print(vx);
        client.print(",");
        client.println(vy);
    }
}

float calculateTiltX(int16_t ax, int16_t ay, int16_t az)
{
    return atan2(ay, az) * 180.0 / PI;
}

float calculateTiltZ(int16_t ax, int16_t ay, int16_t az)
{
    return atan2(ax, az) * 180.0 / PI;
}

