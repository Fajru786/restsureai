import sys
import io
import pandas as pd
import pickle
import warnings
from sklearn.metrics import accuracy_score, classification_report

# Fix Windows console encoding for special characters
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Optional: Suppress harmless warnings
warnings.filterwarnings("ignore", category=UserWarning)

# ===============================
# LOAD DATA
# ===============================
DATASET_PATH = "sleep_predictor/ml/dataset/combined_sleep_disorder_dataset.csv"
data = pd.read_csv(DATASET_PATH)

# ===============================
# CLEAN DATA
# ===============================
# CRITICAL FIX: Fill blank Sleep Disorder cells with "No Sleep Disorder" first!
# Otherwise, dropna() deletes all ~2,750 healthy patients.
data['Sleep Disorder'] = data['Sleep Disorder'].fillna('No Sleep Disorder')

# Now it is safe to drop any actual missing rows
data.dropna(inplace=True)

# Encode Gender
gender_map = {"Male": 0, "Female": 1, "Other": 2}
data["Gender"] = data["Gender"].map(gender_map)

# Encode Occupation
with open("sleep_predictor/ml/occupation_encoder.pkl", "rb") as f:
    occupation_encoder = pickle.load(f)
data["Occupation"] = occupation_encoder.transform(data["Occupation"])

# Encode BMI
bmi_map = {
    "Underweight": 0,
    "Normal": 1,
    "Overweight": 2,
    "Obese": 3
}
data["BMI Category"] = data["BMI Category"].map(bmi_map)

# Convert Blood Pressure (e.g., "120/80" -> 120)
data["Blood Pressure"] = data["Blood Pressure"].str.split("/").str[0].astype(int)

# ===============================
# FEATURES & LABEL
# ===============================
X = data[
    [
        "Gender",
        "Age",
        "Occupation",
        "Sleep Duration",
        "Quality of Sleep",
        "Physical Activity Level",
        "Stress Level",
        "BMI Category",
        "Blood Pressure",
        "Heart Rate",
        "Daily Steps",
    ]
]

y = data["Sleep Disorder"]

# ===============================
# LOAD MODEL, SCALER & ENCODER
# ===============================
with open("sleep_predictor/ml/soft_voting.pkl", "rb") as f:
    model = pickle.load(f)

with open("sleep_predictor/ml/scaler.pkl", "rb") as f:
    scaler = pickle.load(f)

with open("sleep_predictor/ml/label_encoder.pkl", "rb") as f:
    label_encoder = pickle.load(f)

# ===============================
# SCALE & PREDICT
# ===============================
# Must use the scaler so the model understands the numerical ranges
X_scaled = scaler.transform(X)
y_pred = model.predict(X_scaled)

# ===============================
# ACCURACY & REPORT
# ===============================
y_true_encoded = label_encoder.transform(y)

accuracy = accuracy_score(y_true_encoded, y_pred)

print("\n[OK] MODEL ACCURACY:", round(accuracy * 100, 2), "%\n")

print("CLASSIFICATION REPORT:\n")

# Use standard classes from the label encoder
print(classification_report(
    y_true_encoded,
    y_pred,
    target_names=label_encoder.classes_,
    zero_division=0
))