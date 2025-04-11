import numpy as np
import logging
from datetime import datetime
import json
import os
import matplotlib.pyplot as plt

class GestureHandler:
    def __init__(self):
        self.logger = logging.getLogger('AirMouse.Gesture')
        self.recording = False
        self.current_gesture = None
        self.current_data = []
        self.gestures = {}
        self.model = None
        self.scaler = None
        self.callback = None

        # Create gestures directory if it doesn't exist
        self.gestures_dir = "gestures"
        if not os.path.exists(self.gestures_dir):
            os.makedirs(self.gestures_dir)

    def set_callback(self, callback):
        """Set callback for recognized gestures"""
        self.callback = callback

    def start_recording(self, gesture_name):
        """Start recording a gesture"""
        self.recording = True
        self.current_gesture = gesture_name
        self.current_data = []
        for i in range(5):  # Record each gesture 5 times
            print(f"Recording sample {i+1} for gesture {gesture_name}")
        self.logger.info(f"Started recording gesture: {gesture_name}")
        return True

    def stop_recording(self):
        """Stop recording a gesture"""
        self.recording = False
        if self.current_gesture and self.current_data:
            print(f"\n=== DEBUG: Recorded data for {self.current_gesture} ===")
            print(f"Number of samples: {len(self.current_data)}")
            print(f"Sample shape: {np.array(self.current_data).shape}")
            print("First sample:", self.current_data[0])
            print("Last sample:", self.current_data[-1])
            self.gestures[self.current_gesture] = self.current_data.copy()
            samples = len(self.current_data)
            self.logger.info(f"Stopped recording gesture: {self.current_gesture} with {samples} samples")

            # Save gesture to file
            self.save_gesture(self.current_gesture, self.current_data)

            self.current_gesture = None
            return samples
        return 0

    def get_current_samples(self):
        """Get the number of samples recorded so far"""
        return len(self.current_data)

    def get_gestures(self):
        """Get the list of recorded gestures"""
        return list(self.gestures.keys())

    def process_data(self, data):
        """Process incoming sensor data"""
        try:
            if data.startswith("GESTURE,"):
                parts = data.split(',')
                if len(parts) >= 7:  # Format: GESTURE,gx,gy,gz,ax,ay,az
                    gx = float(parts[1])
                    gy = float(parts[2])
                    gz = float(parts[3])
                    ax = float(parts[4])
                    ay = float(parts[5])
                    az = float(parts[6])

                    # If recording, add to current gesture data
                    if self.recording and self.current_gesture:
                        self.current_data.append([gx, gy, gz, ax, ay, az])
                        print(f"Recorded sample: {len(self.current_data)}")

                    # If model is trained, predict gesture
                    elif self.model is not None:
                        self.predict_gesture([gx, gy, gz, ax, ay, az])

            elif data.startswith("GESTURE_DETECTED,"):
                # Direct gesture detection from ESP32
                gesture = data.split(',')[1].strip()
                print(f"ESP32 detected gesture: {gesture}")
                if self.callback:
                    self.callback(gesture)

        except Exception as e:
            self.logger.error(f"Error processing gesture data: {e}")
            print(f"Gesture processing error: {e}")

    def save_gesture(self, name, data):
        """Save a recorded gesture to file"""
        try:
            gesture_file = os.path.join(self.gestures_dir, f"{name}.json")
            with open(gesture_file, 'w') as f:
                json.dump({
                    'name': name,
                    'data': data,
                    'timestamp': datetime.now().isoformat()
                }, f)
            self.logger.info(f"Saved gesture to file: {gesture_file}")
            return True
        except Exception as e:
            self.logger.error(f"Error saving gesture: {e}")
            return False

    def load_gestures(self):
        """Load all saved gestures from files"""
        try:
            self.gestures.clear()

            for filename in os.listdir(self.gestures_dir):
                if filename.endswith('.json'):
                    gesture_file = os.path.join(self.gestures_dir, filename)
                    with open(gesture_file, 'r') as f:
                        gesture_data = json.load(f)
                        self.gestures[gesture_data['name']] = gesture_data['data']

            self.logger.info(f"Loaded {len(self.gestures)} gestures")
            return True
        except Exception as e:
            self.logger.error(f"Error loading gestures: {e}")
            return False

    def train_model(self):
        """Train the gesture recognition model with enhanced features"""
        try:
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.preprocessing import StandardScaler
            from sklearn.model_selection import cross_val_score

            print("\n=== DEBUG: Available Gestures ===")
            for gesture, data in self.gestures.items():
                data_array = np.array(data)
                print(f"{gesture}: {len(data)} samples, shape {data_array.shape}")

            # Check we have at least 2 gestures with samples
            if len(self.gestures) < 2:
                print("Need at least 2 different gestures")
                return False

            if len(self.gestures) < 2:
                self.logger.error("Need at least 2 gestures to train model")
                return False

            # Prepare data with enhanced features
            X = []
            y = []

            for gesture, data in self.gestures.items():
                # Convert to numpy array if not already
                data_array = np.array(data)

                # Extract features from each sample in the gesture
                for sample in data_array:
                    features = self.extract_features([sample])
                    if features is not None:
                        X.append(features[0])
                        y.append(gesture)
            # Debug training data
            print("\n=== DEBUG: Training Data ===")
            print(f"Total samples: {len(X)}")
            print(f"Feature vector length: {len(X[0]) if X else 0}")
            print(f"Class distribution: {np.unique(y, return_counts=True)}")

            if len(X) < 10:  # Need sufficient samples
                self.logger.error("Not enough training samples")
                return False

            # Convert to numpy arrays
            X = np.array(X)
            y = np.array(y)

            print(f"Training data shape: X={X.shape}, y={y.shape}")
            print(f"Gesture classes: {np.unique(y)}")

            # Scale features
            self.scaler = StandardScaler()
            X_scaled = self.scaler.fit_transform(X)

            # Train model with cross-validation
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                class_weight='balanced'
            )

            # Check cross-validation accuracy
            scores = cross_val_score(self.model, X_scaled, y, cv=5)
            print(f"Cross-validation scores: {scores}")
            print(f"Mean CV accuracy: {np.mean(scores):.2f}")

            # Final training
            self.model.fit(X_scaled, y)

            # Feature importance
            print("Feature importances:", self.model.feature_importances_)

            # Test on training data
            train_acc = self.model.score(X_scaled, y)
            print(f"Training accuracy: {train_acc:.2f}")

            self.logger.info("Model trained successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error training model: {e}")
            print(f"Training error: {e}")
            return False

    def extract_features(self, gesture_data):
        """Simpler feature extraction that always works"""
        try:
            if not gesture_data:
                return None

            # Convert to numpy array and flatten
            data = np.array(gesture_data).flatten()

            # Just use raw values as features
            return [data.tolist()]

        except Exception as e:
            print(f"Feature extraction error: {e}")
            return None
    
    def predict_gesture(self, sensor_data):
        """Predict gesture with confidence threshold"""
        try:
            if self.model is None or self.scaler is None:
                print("Model not ready for prediction")
                return None

            # Create input data window
            window = [sensor_data]

            # Extract features
            features = self.extract_features(window)
            if features is None:
                print("Feature extraction failed")
                return None

            # Scale features
            features_scaled = self.scaler.transform(features)

            # Get prediction probabilities
            proba = self.model.predict_proba(features_scaled)[0]
            max_proba = np.max(proba)
            gesture = self.model.classes_[np.argmax(proba)]

            print(f"Prediction probabilities: {dict(zip(self.model.classes_, proba))}")
            print(f"Max probability: {max_proba:.2f}")

            # Only accept predictions with sufficient confidence
            if max_proba > 0.7:  # 70% confidence threshold
                print(f"Confident prediction: {gesture} ({max_proba:.2f})")
                if self.callback:
                    self.callback(gesture)
                return gesture
            else:
                print(f"Low confidence: {gesture} ({max_proba:.2f}) - ignoring")
                return None

        except Exception as e:
            self.logger.error(f"Prediction error: {e}")
            return None

    def recognize_gesture(self, data):
        """Recognize a gesture from provided data"""
        try:
            if self.model is None or self.scaler is None:
                self.logger.error("Model not trained yet")
                return None

            # Extract features from the data
            features = self.extract_features(data)
            if features is None:
                return None

            # Scale features
            features_scaled = self.scaler.transform(features)

            # Make prediction
            prediction = self.model.predict(features_scaled)[0]

            self.logger.info(f"Recognized gesture: {prediction}")
            return prediction

        except Exception as e:
            self.logger.error(f"Error recognizing gesture: {e}")
            print(f"Recognition error: {e}")
            return None