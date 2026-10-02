import apiClient from "./client";

export async function getExplainability(region, leadDay) {
  const config = leadDay === undefined
    ? undefined
    : { params: { lead_day: leadDay } };
  const response = await apiClient.get(
    `/explain/${encodeURIComponent(region)}`,
    config,
  );

  return response.data;
}
