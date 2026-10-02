import apiClient from "./client";

export async function getDashboardSummary(leadDay = 5) {
  const response = await apiClient.get("/dashboard-summary", {
    params: { lead_day: leadDay },
  });

  return response.data;
}

export async function getRiskMap(leadDay = 5) {
  const response = await apiClient.get("/risk-map", {
    params: { lead_day: leadDay },
  });

  return response.data;
}
