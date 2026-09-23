import { useEffect, useState, useCallback } from "react";
import MapView from "../components/MapView.jsx";
import RiskLegend from "../components/RiskLegend.jsx";
import ZonePanel from "../components/ZonePanel.jsx";
import PhoneOptIn from "../components/PhoneOptIn.jsx";
import ReportForm from "../components/ReportForm.jsx";
import Tabs from "../components/Tabs.jsx";
import { api } from "../api.js";

const POLL_MS = 15000;

const TABS = [
  { id: "zone", label: "Zone" },
  { id: "alerts", label: "Alerts" },
  { id: "report", label: "Report" },
];

export default function Home() {
  const [zones, setZones] = useState([]);
  const [selectedZoneId, setSelectedZoneId] = useState(null);
  const [userPosition, setUserPosition] = useState(null);
  const [distanceKm, setDistanceKm] = useState(null);
  const [locationStatus, setLocationStatus] = useState("locating"); // locating | found | denied
  const [activeTab, setActiveTab] = useState("zone");

  const refreshZones = useCallback(async () => {
    try {
      const data = await api.listZones();
      setZones(data);
    } catch {
      // network error - keep showing stale data if any
    }
  }, []);

  useEffect(() => {
    refreshZones();
    const interval = setInterval(refreshZones, POLL_MS);
    return () => clearInterval(interval);
  }, [refreshZones]);

  useEffect(() => {
    if (!navigator.geolocation) {
      setLocationStatus("denied");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const { latitude, longitude } = pos.coords;
        setUserPosition([latitude, longitude]);
        setLocationStatus("found");
        try {
          const nearest = await api.nearestZone(latitude, longitude);
          setSelectedZoneId(nearest.zone_id);
          setDistanceKm(nearest.distance_km);
        } catch {
          // ignore; user can still pick a zone manually
        }
      },
      () => setLocationStatus("denied"),
      { timeout: 8000 }
    );
  }, []);

  // Fall back to the first zone once loaded if geolocation never resolves one
  useEffect(() => {
    if (!selectedZoneId && zones.length > 0) {
      setSelectedZoneId(zones[0].zone_id);
    }
  }, [zones, selectedZoneId]);

  const selectedZone = zones.find((z) => z.zone_id === selectedZoneId);

  return (
    <div className="home-layout">
      <div className="map-wrap">
        <MapView
          zones={zones}
          userPosition={userPosition}
          selectedZoneId={selectedZoneId}
          onSelectZone={(id) => {
            setSelectedZoneId(id);
            setDistanceKm(null);
          }}
        />
        <RiskLegend />
      </div>
      <div className="side-panel">
        <Tabs tabs={TABS} active={activeTab} onChange={setActiveTab} />
        <div className="tab-content">
          {locationStatus === "locating" && (
            <p className="msg" style={{ marginBottom: 12 }}>Detecting your location...</p>
          )}
          {locationStatus === "denied" && (
            <p className="msg error" style={{ marginBottom: 12 }}>
              Couldn't access your location — pick your zone manually below.
            </p>
          )}
          {!selectedZone && <p className="zone-sub">Loading zones...</p>}

          {selectedZone && activeTab === "zone" && (
            <ZonePanel
              zone={selectedZone}
              zones={zones}
              onChangeZone={(id) => {
                setSelectedZoneId(id);
                setDistanceKm(null);
              }}
              distanceKm={distanceKm ?? undefined}
            />
          )}
          {selectedZone && activeTab === "alerts" && <PhoneOptIn zone={selectedZone} />}
          {selectedZone && activeTab === "report" && (
            <ReportForm zone={selectedZone} userPosition={userPosition} />
          )}
        </div>
      </div>
    </div>
  );
}
