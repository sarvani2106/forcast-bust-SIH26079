import apiClient from "./client";

export async function getTrend(region, leadDay) {
  const config = leadDay === undefined
    ? undefined
    : { params: { lead_day: leadDay } };
  const response = await apiClient.get(
    `/trend/${encodeURIComponent(region)}`,
    config,
  );

  return response.data;
}
