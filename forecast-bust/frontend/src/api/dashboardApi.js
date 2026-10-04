import apiClient from "./client";

export async function getRiskMap(leadDay = 5) {
  const response = await apiClient.get("/real/risk-map", {
    params: { lead_day: leadDay },
  });

  return response.data;
}

export function summarizeRiskMap(data) {
  const points = Array.isArray(data?.points) ? data.points : [];
  const count = (risk) => points.filter((point) => point.risk === risk).length;
  const probabilities = points.map((point) => point.bust_probability).filter(Number.isFinite);
  return {
    total_points: data?.total_points ?? points.length,
    high_risk_count: count("HIGH"),
    moderate_risk_count: count("MODERATE"),
    low_risk_count: count("LOW"),
    average_bust_probability: probabilities.length
      ? probabilities.reduce((sum, value) => sum + value, 0) / probabilities.length
      : null,
  };
}
