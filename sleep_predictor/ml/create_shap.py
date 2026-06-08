import shap
import pickle
import pandas as pd

model = pickle.load(open("sleep_predictor/ml/soft_voting.pkl", "rb"))
scaler = pickle.load(open("sleep_predictor/ml/scaler.pkl", "rb"))

# Background data (small sample)
X_background = pd.read_csv(
    "sleep_predictor/ml/dataset/expanded_sleep_health_dataset.csv"
).head(50)

X_background = X_background[[
    "Gender","Age","Occupation","Sleep Duration","Quality of Sleep",
    "Physical Activity Level","Stress Level","BMI Category",
    "Blood Pressure","Heart Rate","Daily Steps"
]]

X_background = scaler.transform(X_background)

explainer = shap.KernelExplainer(model.predict, X_background)

pickle.dump(explainer, open("sleep_predictor/ml/shap_explainer.pkl", "wb"))

print("SHAP explainer saved")
