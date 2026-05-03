import os
import joblib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(BASE_DIR, "models", "fan_model.pkl")

MODEL = joblib.load(model_path)