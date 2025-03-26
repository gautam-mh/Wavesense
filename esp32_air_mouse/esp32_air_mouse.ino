#include <Wire.h>
#include <MPU6050.h>

MPU6050 mpu;
int16_t ax, ay, az, gx, gy, gz;
int vx, vy;
int gx_offset = 0;
int gz_offset = 0;
bool isCalibrating = false;
bool isInitialized = false;
bool isFirstConnect = true;
bool isGestureMode = false;

// Gesture thresholds (from Arduino example)
const int THRESHOLD_LOW = 80;
const int THRESHOLD_HIGH = 145;
const int NEUTRAL_LOW = 100;
const int NEUTRAL_HIGH = 170;

// Calibration settings
const int CALIBRATION_SAMPLES = 100;
const int SAMPLE_DELAY = 10;
const int MOVEMENT_THRESHOLD = 1000;

// Pin definitions
const int SDA_PIN = 21;
const int SCL_PIN = 22;

// Last gesture tracking
unsigned long lastGestureTime = 0;
const unsigned long GESTURE_COOLDOWN = 500;

void setup() {
    Serial.begin(115200);
    delay(1000);
    
    Wire.begin(SDA_PIN, SCL_PIN);
    Serial.println("Initializing MPU6050...");
    
    mpu.initialize();
    
    if (!mpu.testConnection()) {
        Serial.println("MPU6050 connection failed!");
        while (1) {
            delay(1000);
        }
    }
    
    mpu.setFullScaleGyroRange(MPU6050_GYRO_FS_1000);
    mpu.setDLPFMode(MPU6050_DLPF_BW_20);
    
    Serial.println("MPU6050 connection successful!");
    Serial.println("INIT_COMPLETE");
    
    isInitialized = true;
    isFirstConnect = true;
}

void loop() {
    if (isFirstConnect) {
        Serial.println("INIT_COMPLETE");
        delay(100);
        isFirstConnect = false;
    }

    if (Serial.available() > 0) {
        String command = Serial.readStringUntil('\n');
        command.trim();
        
        if (command == "INIT_CHECK") {
            Serial.println("INIT_COMPLETE");
        }
        else if (command == "CALIBRATE") {
            calibrateSensor();
        }
        else if (command == "GESTURE_MODE") {
            isGestureMode = true;
            isCalibrating = false;
            Serial.println("MODE_GESTURE");
        }
        else if (command == "CURSOR_MODE") {
            isGestureMode = false;
            isCalibrating = false;
            Serial.println("MODE_CURSOR");
        }
    }

    if (!isCalibrating && isInitialized) {
        if (isGestureMode) {
            handleGestureMode();
        } else {
            sendMotionData();  // Keep existing cursor control
        }
    }
    
    delay(20);
}

void handleGestureMode() {
    // Get motion data
    mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);
    
    // Map acceleration values exactly like the Arduino example
    byte mappedX = map(ax, -17000, 17000, 0, 255);
    byte mappedY = map(ay, -17000, 17000, 0, 255);
    
    // Debug output (optional)
    Serial.print("DEBUG,X=");
    Serial.print(mappedX);
    Serial.print(",Y=");
    Serial.println(mappedY);
    
    // Apply cooldown to prevent rapid gesture triggers
    unsigned long currentTime = millis();
    if (currentTime - lastGestureTime < GESTURE_COOLDOWN) {
        return;
    }
    
    // Check for gestures using the same logic as the Arduino example
    if (mappedY < THRESHOLD_LOW) {
        Serial.println("GESTURE,DOWN");  // gesture 1
        lastGestureTime = currentTime;
    }
    else if (mappedY > THRESHOLD_HIGH) {
        Serial.println("GESTURE,UP");  // gesture 2
        lastGestureTime = currentTime;
    }
    else if (mappedX > THRESHOLD_HIGH) {
        Serial.println("GESTURE,LEFT");  // gesture 3
        lastGestureTime = currentTime;
    }
    else if (mappedX < THRESHOLD_LOW) {
        Serial.println("GESTURE,RIGHT");  // gesture 4
        lastGestureTime = currentTime;
    }
    else if (mappedX > NEUTRAL_LOW && mappedX < NEUTRAL_HIGH && 
             mappedY > THRESHOLD_LOW && mappedY < 130) {
        Serial.println("GESTURE,SLIGHT_DOWN");  // gesture 5
        lastGestureTime = currentTime;
    }
}

// Keep existing calibration and cursor functions
void calibrateSensor() {
    Serial.println("CALIBRATION_START");
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
        Serial.print("CALIBRATION_PROGRESS,");
        Serial.println(progress);
        
        delay(SAMPLE_DELAY);
    }
    
    if (valid_samples > 0) {
        gx_offset = gx_sum / valid_samples;
        gz_offset = gz_sum / valid_samples;
    }
    
    isCalibrating = false;
    Serial.println("CALIBRATION_COMPLETE");
}

void sendMotionData() {
    mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);
    
    vx = -((gx - gx_offset) / 150);
    vy = ((gz - gz_offset) / 150);
    
    Serial.print("CURSOR,");
    Serial.print(vx);
    Serial.print(",");
    Serial.println(vy);
}