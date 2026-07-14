import os
import sys
import numpy as np
from flask import Flask, render_template, request
from tensorflow.keras.models import load_model
from PIL import Image
import random

# -------- SUPPRESS TENSORFLOW AND PRINT OUTPUT --------
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress TF logging

class DummyFile(object):
    def write(self, x): pass
    def flush(self): pass

sys.stdout = DummyFile()
sys.stderr = DummyFile()

# -------- CONFIG --------
app = Flask(__name__)
MODEL_PATH = "model/best_model.h5"  # Path to your trained model
ESP32_LINK = "http://192.168.0.100"  # Replace with your ESP32 IP
IMG_SIZE = 128

# -------- LOAD MODEL --------
model = load_model(MODEL_PATH)

# -------- CLASS NAMES --------
class_names = [
    "Tomato_Bacterial_Spot",
    "Tomato_Early_Blight",
    "Tomato_Late_Blight",
    "Tomato_Leaf_Mold",
    "Tomato_Septoria_Leaf_Spot",
    "Tomato_Spider_Mites",
    "Tomato_Target_Spot",
    "Tomato_Yellow_Leaf_Curl_Virus",
    "Tomato_Mosaic_Virus",
    "Tomato_Healthy"
]

# -------- FUNCTION TO SIMULATE SENSOR DATA --------
def get_sensor_data():
    return {
        "temperature": round(random.uniform(22, 34), 2),
        "humidity": round(random.uniform(60, 85), 2),
        "soil_moisture": round(random.uniform(45, 70), 2),
        "light": round(random.uniform(200, 900), 2)
    }

# -------- ROUTES --------
@app.route("/")
def home():
    sensor_data = get_sensor_data()
    return render_template("index.html", sensor_data=sensor_data, result=None, img_path=None, esp32_link=ESP32_LINK)

@app.route("/predict", methods=["POST"])
def predict():
    sensor_data = get_sensor_data()

    if "file" not in request.files:
        return render_template("index.html", result="No file uploaded", sensor_data=sensor_data, esp32_link=ESP32_LINK)

    file = request.files["file"]
    if file.filename == "":
        return render_template("index.html", result="No file selected", sensor_data=sensor_data, esp32_link=ESP32_LINK)

    # Save uploaded image
    file_path = os.path.join("static", file.filename)
    try:
        file.save(file_path)
    except OSError as e:
        return render_template("index.html", result=f"Error saving file: {e}", sensor_data=sensor_data, esp32_link=ESP32_LINK)

    # Preprocess image
    try:
        img = Image.open(file_path).convert("RGB").resize((IMG_SIZE, IMG_SIZE))
        img_array = np.expand_dims(np.array(img) / 255.0, axis=0)

        # Temporarily disable stdout/stderr during prediction
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        sys.stdout = DummyFile()
        sys.stderr = DummyFile()
        prediction = model.predict(img_array)
        sys.stdout = original_stdout
        sys.stderr = original_stderr

        predicted_class = class_names[np.argmax(prediction)]
    except Exception as e:
        return render_template("index.html", result=f"Prediction failed: {e}", sensor_data=sensor_data, esp32_link=ESP32_LINK)

    return render_template(
        "index.html",
        result=f"🌿 Predicted Disease: {predicted_class}",
        img_path=file_path,
        sensor_data=sensor_data,
        esp32_link=ESP32_LINK
    )

if __name__ == "__main__":
    app.run(debug=True)