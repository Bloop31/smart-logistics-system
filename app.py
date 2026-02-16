import streamlit as st
import pandas as pd
import numpy as np
import joblib

from decision_engine import (
    classify_risk,
    get_action,
    calculate_baseline_eta,
    calculate_optimized_eta,
    generate_notification
)

# ======================================
# PAGE CONFIG
# ======================================

st.set_page_config(page_title="Smart Logistics System", layout="centered")

st.title("🚚 Smart Logistics Risk Intelligence System")
st.write("Enter shipment details to assess delivery risk and ETA optimization.")

# ======================================
# LOAD MODEL & SCALER
# ======================================

model = joblib.load("models/delay_model.pkl")
scaler = joblib.load("models/scaler.pkl")

# ======================================
# LOAD SYSTEM DATA (FOR MEANS & CONSTANTS)
# ======================================

df_system = pd.read_csv("E:/Projects/Smart-Logistics-System/data/processed/dataset_with_risk_levels.csv")

# Training feature order (EXACTLY as used in model training)
training_features = [
    'Latitude', 'Longitude', 'Inventory_Level', 'Temperature', 'Humidity',
    'Precipitation(mm)', 'Waiting_Time', 'User_Transaction_Amount',
    'User_Purchase_Frequency', 'Asset_Utilization', 'Demand_Forecast',
    'hour', 'day_of_week', 'peak_hour',
    'Traffic_Status_Detour', 'Traffic_Status_Heavy',
    'Asset_ID_Truck_10', 'Asset_ID_Truck_2', 'Asset_ID_Truck_3',
    'Asset_ID_Truck_4', 'Asset_ID_Truck_5', 'Asset_ID_Truck_6',
    'Asset_ID_Truck_7', 'Asset_ID_Truck_8', 'Asset_ID_Truck_9',
    'Asset_ID_Truck_10'
]

# Compute feature means
feature_means = df_system[training_features].mean()

# Operational baseline time
operational_base_time = df_system["Waiting_Time"].mean()

# Reconstruct traffic level
df_system["traffic_level"] = df_system.apply(
    lambda row: "Heavy" if row["Traffic_Status_Heavy"] == 1
    else ("Detour" if row["Traffic_Status_Detour"] == 1 else "Clear"),
    axis=1
)

traffic_impact = (
    df_system.groupby("traffic_level")["delay_probability"]
    .mean()
)

clear_factor = traffic_impact.min()

# ======================================
# USER INPUTS (Only Important Ones)
# ======================================

latitude = st.number_input("Latitude", value=19.0760)
longitude = st.number_input("Longitude", value=72.8777)

traffic = st.selectbox("Traffic Level", ["Clear", "Detour", "Heavy"])

asset_utilization = st.slider(
    "Asset Utilization (%)",
    min_value=50,
    max_value=100,
    value=75
)

precipitation = st.slider(
    "Precipitation (mm)",
    min_value=0,
    max_value=50,
    value=10
)

waiting_time = st.slider(
    "Expected Waiting Time (minutes)",
    min_value=10,
    max_value=60,
    value=30
)

hour = st.slider("Hour of Day", 0, 23, 14)
peak_hour = 1 if hour in [8,9,10,17,18,19] else 0

# ======================================
# ANALYSIS
# ======================================

if st.button("Analyze Shipment"):

    # Get exact training feature order
    training_features = scaler.feature_names_in_

    # Start with mean values for all features
    feature_means = df_system[training_features].mean()

    # Create base input row
    input_data = pd.DataFrame([feature_means], columns=training_features)

    # Overwrite with user inputs
    input_data["Latitude"] = latitude
    input_data["Longitude"] = longitude
    input_data["Precipitation(mm)"] = precipitation
    input_data["Waiting_Time"] = waiting_time
    input_data["Asset_Utilization"] = asset_utilization
    input_data["hour"] = hour
    input_data["peak_hour"] = peak_hour

    # Encode traffic
    
    input_data["Traffic_Status_Heavy"] = 0
    input_data["Traffic_Status_Detour"] = 0

    if traffic == "Heavy":
        input_data["Traffic_Status_Heavy"] = 1
    elif traffic == "Detour":
        input_data["Traffic_Status_Detour"] = 1


    # Ensure correct column order
    input_data = input_data[training_features]

    # Scale
    scaled_data = scaler.transform(input_data)

    # Predict
    delay_probability = model.predict_proba(scaled_data)[0][1]


    # ==================================
    # DECISION ENGINE
    # ==================================

    risk = classify_risk(delay_probability)

    baseline_eta = calculate_baseline_eta(
        delay_probability,
        operational_base_time
    )

    optimized_eta = calculate_optimized_eta(
        delay_probability,
        risk,
        operational_base_time,
        clear_factor
    )

    action = get_action(risk, asset_utilization)

    message = generate_notification(
        risk,
        baseline_eta,
        optimized_eta,
        traffic
    )

    # ==================================
    # DISPLAY
    # ==================================

    st.subheader("📊 Analysis Results")

    st.write("**Delay Probability:**", round(delay_probability, 3))
    st.write("**Risk Level:**", risk)
    st.write("**Action Taken:**", action)
    st.write("**Baseline ETA:**", round(baseline_eta, 2), "minutes")
    st.write("**Optimized ETA:**", round(optimized_eta, 2), "minutes")

    if risk in ["High", "Critical"]:
        st.error("⚠ Shipment delay risk detected.")
    elif risk == "Medium":
        st.warning("🟡 Moderate risk detected. Monitoring active.")
    else:
        st.success("🟢 Shipment is on schedule.")

    st.subheader("📩 Customer Notification")
    st.info(message)
