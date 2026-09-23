import { MapContainer, TileLayer, CircleMarker, Popup, Marker, useMap } from "react-leaflet";
import { useEffect } from "react";
import L from "leaflet";

const RISK_COLOR = { Low: "#3d7a4d", Medium: "#a06a1f", High: "#b3372c" };
const ODISHA_CENTER = [20.6, 85.5];

const userIcon = L.divIcon({
  className: "",
  html: `<div style="width:14px;height:14px;border-radius:50%;background:#171717;border:3px solid white;box-shadow:0 0 4px rgba(0,0,0,0.4);"></div>`,
  iconSize: [14, 14],
  iconAnchor: [7, 7],
});

function Recenter({ position }) {
  const map = useMap();
  useEffect(() => {
    if (position) map.setView(position, 12, { animate: true });
  }, [position]);
  return null;
}

export default function MapView({ zones, userPosition, selectedZoneId, onSelectZone }) {
  return (
    <MapContainer center={ODISHA_CENTER} zoom={7} style={{ height: "100%", width: "100%" }}>
      <TileLayer
        attribution='&copy; OpenStreetMap contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {userPosition && (
        <>
          <Marker position={userPosition} icon={userIcon}>
            <Popup>Your location</Popup>
          </Marker>
          <Recenter position={userPosition} />
        </>
      )}
      {zones.map((zone) => {
        const level = zone.risk?.level || "Low";
        const isSelected = zone.zone_id === selectedZoneId;
        return (
          <CircleMarker
            key={zone.zone_id}
            center={[zone.lat, zone.lon]}
            radius={isSelected ? 14 : 9}
            pathOptions={{
              color: isSelected ? "#171717" : "#ffffff",
              weight: isSelected ? 3 : 1,
              fillColor: RISK_COLOR[level],
              fillOpacity: 0.85,
            }}
            eventHandlers={{ click: () => onSelectZone(zone.zone_id) }}
          >
            <Popup>
              <strong>{zone.name}</strong>
              <br />
              {zone.city}
              <br />
              Risk: <strong>{level}</strong>
            </Popup>
          </CircleMarker>
        );
      })}
    </MapContainer>
  );
}
