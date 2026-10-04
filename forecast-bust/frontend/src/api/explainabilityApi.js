import apiClient from "./client";

export async function getRealExplainability(latitude, longitude, leadDay) {
  const response = await apiClient.get("/real/explain", {
    params: { latitude, longitude, lead_day: leadDay },
  });
  return response.data;
}
