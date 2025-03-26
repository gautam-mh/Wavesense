"""
Configuration file for Gesture Control System
Contains all configurable parameters and settings
"""

import os

# Directory Structure
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
RAW_DATA_DIR = os.path.join(DATA_DIR, 'raw')
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, 'processed')
MODEL_DIR = os.path.join(BASE_DIR, 'models')
LOG_DIR = os.path.join(BASE_DIR, 'logs')

# Ensure directories exist
for directory in [DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, MODEL_DIR, LOG_DIR]:
    os.makedirs(directory, exist_ok=True)

# Data Collection Parameters
SAMPLE_RATE = 100  # Hz
SAMPLE_DURATION = 2.0  # seconds
SAMPLES_PER_GESTURE = 50  # Number of samples to collect per gesture
CALIBRATION_DURATION = 3  # seconds

# Feature Extraction Parameters
WINDOW_SIZE = 100  # samples
OVERLAP = 0.5  # 50% overlap between windows
MIN_SAMPLES_FOR_FEATURE = 50

# Sensor Parameters
GYRO_SENSITIVITY = 250  # degrees per second
ACCEL_SENSITIVITY = 2  # g
SENSOR_RANGE = {
    'gyro_x': (-250, 250),
    'gyro_y': (-250, 250),
    'gyro_z': (-250, 250),
    'acc_x': (-2, 2),
    'acc_y': (-2, 2),
    'acc_z': (-2, 2)
}

# Serial Communication
SERIAL_BAUDRATE = 115200
SERIAL_TIMEOUT = 1.0
COMMAND_TERMINATOR = '\n'
DATA_DELIMITER = ','

# Gesture Recognition
SUPPORTED_GESTURES = [
    'click',
    'double_click',
    'right_click',
    'scroll_up',
    'scroll_down',
    'swipe_left',
    'swipe_right',
    'circle'
]

# Model Parameters
MODEL_PARAMS = {
    'random_forest': {
        'n_estimators': 100,
        'max_depth': 10,
        'min_samples_split': 2,
        'min_samples_leaf': 1,
        'random_state': 42
    },
    'svm': {
        'kernel': 'rbf',
        'C': 1.0,
        'gamma': 'scale',
        'random_state': 42
    },
    'neural_network': {
        'hidden_layer_sizes': (100, 50),
        'activation': 'relu',
        'solver': 'adam',
        'max_iter': 1000,
        'random_state': 42
    }
}

# GUI Configuration
GUI_CONFIG = {
    'window_title': 'Gesture Control System',
    'window_size': '800x600',
    'theme': 'light',  # or 'dark'
    'font': {
        'family': 'Helvetica',
        'size': 10,
        'title_size': 12,
        'header_size': 14
    },
    'colors': {
        'primary': '#007bff',
        'secondary': '#6c757d',
        'success': '#28a745',
        'danger': '#dc3545',
        'warning': '#ffc107',
        'info': '#17a2b8',
        'light': '#f8f9fa',
        'dark': '#343a40'
    }
}

# Cursor Control Parameters
CURSOR_CONFIG = {
    'sensitivity': 2.0,
    'smoothing_factor': 0.3,
    'dead_zone': 0.1,
    'max_speed': 1000,
    'acceleration': 1.5
}

# Training Parameters
TRAINING_CONFIG = {
    'validation_split': 0.2,
    'test_split': 0.1,
    'batch_size': 32,
    'epochs': 50,
    'early_stopping_patience': 5,
    'learning_rate': 0.001
}

# Logging Configuration
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
        'detailed': {
            'format': '%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s'
        }
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
        },
        'file': {
            'level': 'DEBUG',
            'formatter': 'detailed',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOG_DIR, 'gesture_control.log'),
            'mode': 'a',
        }
    },
    'loggers': {
        '': {  # root logger
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True
        }
    }
}

# Error Messages
ERROR_MESSAGES = {
    'serial_connection': 'Failed to establish serial connection. Please check the connection and try again.',
    'sensor_initialization': 'Failed to initialize the sensor. Please check the connections and restart the device.',
    'data_collection': 'Error during data collection. Please try again.',
    'model_training': 'Error during model training. Please check the training data and parameters.',
    'gesture_recognition': 'Error during gesture recognition. Please recalibrate the sensor.',
    'file_operation': 'Error during file operation. Please check file permissions and disk space.',
    'invalid_gesture': 'Invalid gesture detected. Please perform the gesture again.',
    'calibration': 'Calibration failed. Please keep the sensor still during calibration.'
}

# Feature Names
FEATURE_NAMES = [
    'mean', 'std', 'max', 'min', 'range',
    'rms', 'variance', 'skewness', 'kurtosis',
    'zero_crossing_rate', 'mean_crossing_rate',
    'correlation_xy', 'correlation_yz', 'correlation_xz',
    'energy', 'entropy'
]

# Save/Load Configuration
SAVE_CONFIG = {
    'model_format': 'h5',
    'data_format': 'csv',
    'compression': True,
    'backup_existing': True,
    'max_backups': 5
}

# Debug Mode
DEBUG = True

# Version Information
VERSION = '1.0.0'
BUILD_DATE = '2024-02-19'