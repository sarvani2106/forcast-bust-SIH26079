import { useEffect, useState } from "react";
import { GeoJSON, MapContainer, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import indiaGeoJsonText from "../../assets/india.geojson?raw";
import regionsGeoJsonText from "../../assets/regions.geojson?raw";
import EmptyState from "../common/EmptyState";
import ErrorState from "../common/ErrorState";
import LoadingState from "../common/LoadingState";

const riskColors = {
  LOW: "#76B7D8",
  MODERATE: "#F2C879",
  HIGH: "#E98B8B",
};

const unknownColor = "#D9E2EC";
const indiaGeoJson = JSON.parse(indiaGeoJsonText);
const regionsGeoJson = JSON.parse(regionsGeoJsonText);
const indiaBounds = L.geoJSON(indiaGeoJson).getBounds();
const monitoredRegionNames = new Set(
  regionsGeoJson.features.map((feature) => feature.properties?.name),
);
const coastalAndhraFeature = regionsGeoJson.features.find(
  (feature) => feature.properties?.name === "Coastal Andhra",
);
const monitoredRegionFeatures = [
  coastalAndhraFeature,
  ...indiaGeoJson.features.filter((feature) =>
    monitoredRegionNames.has(feature.properties?.st_nm),
  ),
].filter(Boolean);
const monitoredRegionsGeoJson = {
  type: "FeatureCollection",
  features: monitoredRegionFeatures,
};

function formatProbability(value) {
  if (value === undefined || value === null) return "No data";

  return typeof value === "number"
    ? new Intl.NumberFormat("en-US", {
        style: "percent",
        maximumFractionDigits: 1,
      }).format(value)
    : value;
}

function getRegionRisk(riskByRegion, regionName) {
  return riskByRegion.get(regionName);
}

function FitGeoJsonBounds() {
  const map = useMap();

  useEffect(() => {
    map.fitBounds(indiaBounds, {
      padding: [18, 18],
      maxZoom: 6,
    });
  }, [map]);

  return null;
}

function RegionLayer({ riskByRegion, selectedRegion, onSelectRegion }) {
  const getStyle = (feature) => {
    const regionName =
      feature.properties?.name || feature.properties?.st_nm;
    const regionData = getRegionRisk(riskByRegion, regionName);
    const risk = regionData?.risk;

    return {
      color: selectedRegion === regionName ? "#1677E8" : "#FFFFFF",
      weight: selectedRegion === regionName ? 3 : 1.5,
      opacity: 1,
      fillColor: riskColors[risk] || unknownColor,
      fillOpacity: 0.85,
    };
  };

  const handleFeature = (feature, layer) => {
    const regionName =
      feature.properties?.name || feature.properties?.st_nm;
    const regionData = getRegionRisk(riskByRegion, regionName);
    const risk = regionData?.risk || "No data";
    const leadDay = regionData?.lead_day ?? "No data";

    layer.bindTooltip(
      `<strong>${regionName || "Unknown region"}</strong><br />` +
        `Risk: ${risk}<br />` +
        `Bust Probability: ${formatProbability(regionData?.bust_probability)}<br />` +
        `Confidence: ${formatProbability(regionData?.confidence)}<br />` +
        `Lead Day: ${leadDay}`,
      {
        direction: "top",
        sticky: true,
        opacity: 0.96,
      },
    );

    layer.on({
      click: () => {
        if (regionName) {
          onSelectRegion(regionName);
        }
      },
      mouseover: (event) => {
        event.target.setStyle({
          weight: 3,
          color: "#1677E8",
        });
        event.target.bringToFront();
      },
      mouseout: (event) => {
        event.target.setStyle(getStyle(feature));
      },
    });
  };

  return (
    <GeoJSON
      key={selectedRegion || "no-selection"}
      data={monitoredRegionsGeoJson}
      style={getStyle}
      onEachFeature={handleFeature}
    />
  );
}

function RiskLegend() {
  return (
    <div className="risk-map-legend" aria-label="Risk map legend">
      <span className="risk-map-legend-title">Risk level</span>
      {[
        ["HIGH", riskColors.HIGH],
        ["MODERATE", riskColors.MODERATE],
        ["LOW", riskColors.LOW],
        ["NO DATA", unknownColor],
      ].map(([label, color]) => (
        <span className="risk-map-legend-item" key={label}>
          <span
            className="risk-map-legend-swatch"
            style={{ backgroundColor: color }}
            aria-hidden="true"
          />
          {label}
        </span>
      ))}
    </div>
  );
}

function RiskMap({ riskMap, leadDay, isLoading, hasError, onSelectRegion }) {
  const [selectedRegion, setSelectedRegion] = useState("");
  const riskRegions = Array.isArray(riskMap?.regions) ? riskMap.regions : [];
  const riskByRegion = new Map(
    riskRegions.map((region) => [region.region, region]),
  );

  const handleSelectRegion = (regionName) => {
    setSelectedRegion(regionName);
    onSelectRegion?.(regionName);
  };

  if (isLoading) {
    return <LoadingState />;
  }

  if (hasError) {
    return <ErrorState message="Unable to load regional risk data." />;
  }

  if (!riskRegions.length) {
    return <EmptyState message="No regional risk data available." />;
  }

  return (
    <div className="risk-map-shell">
      <div className="risk-map-frame">
        <MapContainer
          className="risk-map"
          bounds={indiaBounds}
          boundsOptions={{ padding: [18, 18] }}
          scrollWheelZoom
          aria-label={`Regional forecast risk map for lead day ${leadDay}`}
        >
          <GeoJSON
            data={indiaGeoJson}
            style={() => ({
              color: "#B8CCDC",
              weight: 1,
              opacity: 1,
              fillColor: "#EAF2F7",
              fillOpacity: 1,
            })}
          />
          <FitGeoJsonBounds />
          <RegionLayer
            riskByRegion={riskByRegion}
            selectedRegion={selectedRegion}
            onSelectRegion={handleSelectRegion}
          />
        </MapContainer>
        <RiskLegend />
      </div>
      <p className="risk-map-caption">
        Regional boundaries are sourced from the project GeoJSON. Risk styling
        reflects the selected lead day {leadDay} response.
      </p>
    </div>
  );
}

export default RiskMap;
