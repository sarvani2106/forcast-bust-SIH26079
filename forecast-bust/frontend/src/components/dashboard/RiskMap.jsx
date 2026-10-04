import { memo, useEffect, useMemo, useState } from "react";
import {
  CircleMarker,
  GeoJSON,
  MapContainer,
  Popup,
  useMap,
} from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

import indiaGeoJsonUrl from "../../assets/india.geojson?url";
import EmptyState from "../common/EmptyState";
import ErrorState from "../common/ErrorState";
import LoadingState from "../common/LoadingState";

const riskColors = {
  LOW: "#76B7D8",
  MODERATE: "#F2C879",
  HIGH: "#E98B8B",
};

const unknownColor = "#D9E2EC";

function formatProbability(value) {
  if (value === undefined || value === null) {
    return "No data";
  }

  return typeof value === "number"
    ? new Intl.NumberFormat("en-US", {
        style: "percent",
        maximumFractionDigits: 1,
      }).format(value)
    : value;
}

function formatValue(value, digits = 2) {
  return value == null ? "No data" : typeof value === "number" ? value.toLocaleString("en", { maximumFractionDigits: digits }) : value;
}

function FitGeoJsonBounds({ bounds }) {
  const map = useMap();

  useEffect(() => {
    map.fitBounds(bounds, {
      padding: [18, 18],
      maxZoom: 6,
    });
  }, [bounds, map]);

  return null;
}

function getRiskColor(risk) {
  return riskColors[risk] || unknownColor;
}

function RiskPoints({ points, onSelectPoint }) {
  return (
    <>
      {points.map((point, index) => {
        const riskColor = getRiskColor(point.risk);

        return (
          <CircleMarker
  key={`${point.latitude}-${point.longitude}-${index}`}
  center={[point.latitude, point.longitude]}
  radius={2}
  eventHandlers={{ click: () => onSelectPoint?.(point) }}
  pathOptions={{
    color: riskColor,
    fillColor: riskColor,
    fillOpacity: 0.88,
    weight: 0,
    opacity: 1,
  }}
>
            <Popup>
              <div style={{ minWidth: "210px" }}>
                <strong>
                  Grid Point
                </strong>

                <br />

                Latitude:{" "}
                {Number(point.latitude).toFixed(2)}

                <br />

                Longitude:{" "}
                {Number(point.longitude).toFixed(2)}

                <hr />

                <strong>
                  Risk: {formatValue(point.risk)}
                </strong>

                <br />

                Bust Probability:{" "}
                {formatProbability(
                  point.bust_probability
                )}

                <br />

                Confidence:{" "}
                {formatProbability(
                  point.confidence
                )}

                <br />

                Prediction:{" "}
                {formatValue(point.bust_prediction)}

                <hr />

                Rainfall Forecast:{" "}
                {formatValue(point.rainfall_forecast)} mm

                <br />

                Forecast Revision:{" "}
                {formatValue(point.forecast_revision)} mm

                <br />

                Historical MAE:{" "}
                {formatValue(point.historical_mae)} mm

                <br />

                Forecast Stability:{" "}
                {formatValue(point.forecast_stability, 4)}
              </div>
            </Popup>
          </CircleMarker>
        );
      })}
    </>
  );
}

function RiskLegend() {
  return (
    <div
      className="risk-map-legend"
      aria-label="Risk map legend"
    >
      <span className="risk-map-legend-title">
        Forecast bust risk
      </span>

      {[
        ["HIGH", riskColors.HIGH],
        ["MODERATE", riskColors.MODERATE],
        ["LOW", riskColors.LOW],
        ["NO DATA", unknownColor],
      ].map(([label, color]) => (
        <span
          className="risk-map-legend-item"
          key={label}
        >
          <span
            className="risk-map-legend-swatch"
            style={{
              backgroundColor: color,
            }}
            aria-hidden="true"
          />

          {label}
        </span>
      ))}
    </div>
  );
}

function RiskMap({
  riskMap,
  leadDay,
  isLoading,
  hasError,
  onSelectPoint,
}) {
  const [indiaGeoJson, setIndiaGeoJson] = useState(null);
  const [hasBoundaryError, setHasBoundaryError] = useState(false);
  useEffect(() => {
    let current = true;
    fetch(indiaGeoJsonUrl).then((response) => {
      if (!response.ok) throw new Error("Boundary unavailable");
      return response.json();
    }).then((data) => current && setIndiaGeoJson(data)).catch(() => current && setHasBoundaryError(true));
    return () => { current = false; };
  }, []);
  const indiaBounds = useMemo(() => indiaGeoJson ? L.geoJSON(indiaGeoJson).getBounds() : null, [indiaGeoJson]);
  const points = Array.isArray(riskMap?.points)
    ? riskMap.points
    : [];

  if (isLoading) {
    return <LoadingState />;
  }

  if (hasError) {
    return (
      <ErrorState
        message="Unable to load forecast data."
      />
    );
  }

  if (!points.length) {
    return (
      <EmptyState
        message="No forecast data available for this selection."
      />
    );
  }

  if (hasBoundaryError) return <ErrorState message="Unable to load forecast map boundary." />;
  if (!indiaGeoJson || !indiaBounds) return <LoadingState />;

  return (
    <div className="risk-map-shell">
      <div className="risk-map-frame">
        <MapContainer
          className="risk-map"
          bounds={indiaBounds}
          boundsOptions={{
            padding: [18, 18],
          }}
          scrollWheelZoom
          aria-label={`Real NCMRWF forecast bust risk map for lead day ${leadDay}`}
        >
          {/* India boundary/background */}
          <GeoJSON
            data={indiaGeoJson}
            style={() => ({
              color: "#B8CCDC",
              weight: 1,
              opacity: 1,
              fillColor: "#EAF2F7",
              fillOpacity: 0.55,
            })}
          />

          <FitGeoJsonBounds bounds={indiaBounds} />

          {/* Real ML grid-point predictions rendered as Leaflet CircleMarkers. */}
          <RiskPoints points={points} onSelectPoint={onSelectPoint} />
        </MapContainer>

        <RiskLegend />
      </div>

      <p className="risk-map-caption">
        Historical NCMRWF forecast data · NCMRWF TIGGE + IMD rainfall verification · {points.length.toLocaleString()} grid points · lead day {leadDay}.
      </p>
    </div>
  );
}

export default memo(RiskMap);
