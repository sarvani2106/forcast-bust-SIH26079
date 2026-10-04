import apiClient from "./client";

// Retained for the implemented legacy SHAP endpoint, which is keyed by region.
export async function getRegions() {
  const response = await apiClient.get("/regions");
  return response.data;
}

export async function getPrediction(latitude, longitude, leadDay = 5) {
  const response = await apiClient.get("/real/prediction", {
    params: { latitude, longitude, lead_day: leadDay },
  });

  return response.data;
}

export async function getForecast(latitude, longitude) {
  const response = await apiClient.get("/real/forecast", {
    params: { latitude, longitude },
  });

  return response.data;
}
