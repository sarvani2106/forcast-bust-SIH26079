from backend.real_data import get_latest_by_lead_day
from backend.real_model import predict_real

print("=" * 70)
print("REAL MODEL + BACKEND TEST")
print("=" * 70)

for lead_day in [1, 5, 7, 10]:

    data = get_latest_by_lead_day(lead_day)

    row = data.iloc[0]

    prediction = predict_real(row)

    print(f"\nLead Day: {lead_day}")
    print(f"Latitude : {row['LATITUDE']}")
    print(f"Longitude: {row['LONGITUDE']}")
    print(f"Rainfall : {row['forecast_rainfall']:.2f} mm")

    print(
        f"Bust Probability: "
        f"{prediction['bust_probability'] * 100:.2f}%"
    )

    print(
        f"Confidence: "
        f"{prediction['confidence'] * 100:.2f}%"
    )

    print(f"Risk: {prediction['risk']}")
    print(f"Prediction: {prediction['bust_prediction']}")

print("\nDONE")