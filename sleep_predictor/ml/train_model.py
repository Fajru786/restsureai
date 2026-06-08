import pandas as pd
import pickle

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from xgboost import XGBClassifier

# NEW: Import MLPClassifier for the Artificial Neural Network (ANN)
from sklearn.neural_network import MLPClassifier


# Load dataset
DATASET_PATH = "sleep_predictor/ml/dataset/combined_sleep_disorder_dataset.csv"
data = pd.read_csv(DATASET_PATH)
print("Dataset loaded")


# Initial cleaning
# -----------------------------
# HANDLE TARGET FIRST
# -----------------------------

# Fill missing Sleep Disorder as Healthy
data["Sleep Disorder"] = data["Sleep Disorder"].fillna("No Sleep Disorder")

# Now drop missing values from other columns only
data = data.dropna()

print("Missing values handled correctly")


# Encode Gender
gender_map = {"Male": 0, "Female": 1, "Other": 2}
data["Gender"] = data["Gender"].map(gender_map)


# Encode Occupation
occupation_encoder = LabelEncoder()
data["Occupation"] = occupation_encoder.fit_transform(data["Occupation"])


# Encode BMI Category
bmi_map = {
    "Underweight": 0,
    "Normal": 1,
    "Overweight": 2,
    "Obese": 3
}
data["BMI Category"] = data["BMI Category"].map(bmi_map)


# Convert Blood Pressure (use systolic value)
data["Blood Pressure"] = data["Blood Pressure"].str.split("/").str[0].astype(int)


# Then drop other missing values
# First fill target
data["Sleep Disorder"] = data["Sleep Disorder"].fillna("No Sleep Disorder")

# Then drop other missing values
data = data.dropna()
print("Categorical features encoded")


# Feature selection (ORDER IS CRITICAL)
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


# Encode target labels
label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)
print("Target labels encoded")


# Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
)

print("Encoded Classes:", label_encoder.classes_)

# Feature scaling (important for KNN, SVM, & ANN)
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)
print("Feature scaling completed")


# Define base models 
lr = LogisticRegression(
    max_iter=1000,
    class_weight="balanced"
)

dt = DecisionTreeClassifier(
    random_state=42,
    class_weight="balanced"
)

rf = RandomForestClassifier(
    n_estimators=800,
    max_depth=None,
    class_weight="balanced_subsample",
    random_state=42
)

knn = KNeighborsClassifier(n_neighbors=5)

svm = SVC(
    kernel="rbf",
    probability=True,
    class_weight="balanced"
)

xgb = XGBClassifier(
    random_state=42,
    eval_metric='mlogloss'
)

# NEW: Define Artificial Neural Network (ANN) Model
# Using 2 hidden layers (64 nodes, then 32 nodes) and max_iter=1000 to ensure convergence
ann = MLPClassifier(
    hidden_layer_sizes=(64, 32), 
    max_iter=1000, 
    random_state=42
)


# HARD VOTING ENSEMBLE
hard_voting_model = VotingClassifier(
    estimators=[
        ("lr", lr),
        ("dt", dt),
        ("rf", rf),
        ("knn", knn),
        ("svm", svm),
        ("xgb", xgb),
        ("ann", ann), # NEW: Added to ensemble
    ],
    voting="hard"
)


# SOFT VOTING ENSEMBLE
soft_voting_model = VotingClassifier(
    estimators=[
        ("lr", lr),
        ("dt", dt),
        ("rf", rf),
        ("knn", knn),
        ("svm", svm),
        ("xgb", xgb),
        ("ann", ann), # NEW: Added to ensemble
    ],
    voting="soft",
    weights=[1, 1, 3, 1, 2, 3, 1]
)

models = {
    "Logistic Regression": lr,
    "Decision Tree": dt,
    "Random Forest": rf,
    "KNN": knn,
    "SVM": svm,
    "XGBoost": xgb,
    "ANN (MLP)": ann, # NEW: Added to models dictionary
    "Voting Classifier": soft_voting_model
}

# Train models
lr.fit(X_train, y_train)
dt.fit(X_train, y_train)
rf.fit(X_train, y_train)
knn.fit(X_train, y_train)
svm.fit(X_train, y_train)
xgb.fit(X_train, y_train)
ann.fit(X_train, y_train) # NEW: Train ANN

hard_voting_model.fit(X_train, y_train)
soft_voting_model.fit(X_train, y_train)

print("All models trained successfully")


# Save models & encoders
pickle.dump(lr, open("sleep_predictor/ml/lr_model.pkl", "wb"))
pickle.dump(dt, open("sleep_predictor/ml/dt_model.pkl", "wb"))
pickle.dump(rf, open("sleep_predictor/ml/rf_model.pkl", "wb"))
pickle.dump(knn, open("sleep_predictor/ml/knn_model.pkl", "wb"))
pickle.dump(svm, open("sleep_predictor/ml/svm_model.pkl", "wb"))
pickle.dump(xgb, open("sleep_predictor/ml/xgb_model.pkl", "wb"))
pickle.dump(ann, open("sleep_predictor/ml/ann_model.pkl", "wb")) # NEW: Save ANN

pickle.dump(hard_voting_model, open("sleep_predictor/ml/hard_voting.pkl", "wb"))
pickle.dump(soft_voting_model, open("sleep_predictor/ml/soft_voting.pkl", "wb"))

pickle.dump(label_encoder, open("sleep_predictor/ml/label_encoder.pkl", "wb"))
pickle.dump(scaler, open("sleep_predictor/ml/scaler.pkl", "wb"))
pickle.dump(occupation_encoder, open("sleep_predictor/ml/occupation_encoder.pkl", "wb"))

print("All model files saved successfully")
print("TRAINING COMPLETED")


from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

def evaluate(name, model):
    y_pred = model.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    pre = precision_score(y_test, y_pred, average='weighted')
    rec = recall_score(y_test, y_pred, average='weighted')
    f1  = f1_score(y_test, y_pred, average='weighted')

    print(f"\n{name}")
    print("Accuracy :", acc)
    print("Precision:", pre)
    print("Recall   :", rec)
    print("F1 Score :", f1)


# Evaluate each model
evaluate("Logistic Regression", lr)
evaluate("Decision Tree", dt)
evaluate("Random Forest", rf)
evaluate("KNN", knn)
evaluate("SVM", svm)
evaluate("XGBoost", xgb)
evaluate("ANN (MLP)", ann) # NEW: Evaluate ANN
evaluate("Voting Classifier", soft_voting_model)