import apiClient from "./client";

export async function getRegions() {
  const response = await apiClient.get("/regions");
  return response.data;
}

export async function getPrediction(region, leadDay) {
  const config = leadDay === undefined
    ? undefined
    : { params: { lead_day: leadDay } };
  const response = await apiClient.get(
    `/prediction/${encodeURIComponent(region)}`,
    config,
  );

  return response.data;
}

export async function getForecast(region) {
  const response = await apiClient.get(
    `/forecast/${encodeURIComponent(region)}`,
  );

  return response.data;
}
