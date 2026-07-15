import os
import pickle
import numpy as np
import pandas as pd
from catboost import CatBoostClassifier

# NOTE: This script is an example of how the actual models were generated.
# In a real environment, you would run this script to generate `model_control.pkl`
# and the DL model weights before starting the application.

def generate_control_model():
    print("Generating dummy Control Model (CatBoost)...")
    # Initialize a dummy CatBoost model
    model = CatBoostClassifier(iterations=10, depth=2, learning_rate=1, loss_function='Logloss', verbose=False)
    
    # Train on dummy data
    X = np.random.rand(100, 5)
    y = np.random.randint(2, size=100)
    model.fit(X, y)
    
    # Save model
    model_path = os.path.join(os.path.dirname(__file__), "model_control.pkl")
    with open(model_path, "wb") as f:
        pickle.dump(model, f)
    print(f"Saved control model to {model_path}")

def generate_test_model():
    print("Generating DL Model Weights (PyTorch)...")
    print("For this repository, the DL model is embedded as a Base64 string in app.py to avoid large files.")
    print("In production, PyTorch weights would be loaded via state_dict() from S3 or local storage.")
    
if __name__ == "__main__":
    generate_control_model()
    generate_test_model()
    print("Model generation script finished.")
