import numpy as np


# ======================================
# TRAFFIC LEVEL RECONSTRUCTION
# ======================================

def get_traffic_level(traffic_heavy, traffic_detour):
    if traffic_heavy == 1:
        return "Heavy"
    elif traffic_detour == 1:
        return "Detour"
    else:
        return "Clear"


# ======================================
# RISK CLASSIFICATION
# ======================================

def classify_risk(delay_probability):

    if delay_probability < 0.40:
        return "Low"
    elif delay_probability <= 0.70:
        return "Medium"
    elif delay_probability <= 0.90:
        return "High"
    else:
        return "Critical"


# ======================================
# RISK → ACTION MAPPING
# ======================================

def get_action(risk, asset_utilization):

    if risk == "Low":
        return "Normal"

    elif risk == "Medium":
        return "Monitor"

    elif risk == "High":
        if asset_utilization > 90:
            return "Reroute_Notify_Redistribute"
        else:
            return "Reroute_Notify"

    elif risk == "Critical":
        return "Reroute_Notify_Redistribute"


# ======================================
# BASELINE ETA CALCULATION
# ======================================

def calculate_baseline_eta(delay_probability, operational_base_time):
    return operational_base_time + (delay_probability * operational_base_time)


# ======================================
# DATA-DRIVEN REROUTE OPTIMIZATION
# ======================================

def calculate_optimized_eta(delay_probability,
                             risk,
                             operational_base_time,
                             clear_factor,
                             improvement_rate=0.5):

    baseline_eta = calculate_baseline_eta(delay_probability,
                                          operational_base_time)

    if risk in ["High", "Critical"]:

        optimized_factor = (
            delay_probability
            - improvement_rate * (delay_probability - clear_factor)
        )

        optimized_eta = (
            operational_base_time
            + (optimized_factor * operational_base_time)
        )

        return optimized_eta

    else:
        return baseline_eta


# ======================================
# CUSTOMER NOTIFICATION
# ======================================

def generate_notification(risk,
                          baseline_eta,
                          optimized_eta,
                          traffic_level):

    baseline = round(baseline_eta, 2)
    optimized = round(optimized_eta, 2)

    if risk in ["High", "Critical"]:

        if optimized < baseline:
            return (
                f"Due to {traffic_level} traffic conditions, your shipment faced elevated delay risk. "
                f"We have optimized the route. Updated ETA: {optimized} minutes "
                f"(earlier estimate was {baseline} minutes)."
            )
        else:
            return (
                f"Due to {traffic_level} traffic conditions, your shipment is under high delay risk. "
                f"Our operations team is actively monitoring the situation. "
                f"Current ETA: {baseline} minutes."
            )

    elif risk == "Medium":
        return (
            f"Your shipment is experiencing moderate traffic conditions. "
            f"Our system is monitoring for potential delays."
        )

    else:
        return "Your shipment is on schedule."
