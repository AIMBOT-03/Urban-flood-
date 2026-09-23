import { useCallback, useEffect, useState } from "react";
import AdminOverview from "../components/AdminOverview.jsx";
import ReportsTable from "../components/ReportsTable.jsx";
import ActionLog from "../components/ActionLog.jsx";
import Tabs from "../components/Tabs.jsx";
import { api } from "../api.js";

const POLL_MS = 10000;

const TABS = [
  { id: "overview", label: "Overview" },
  { id: "reports", label: "Citizen Reports" },
  { id: "log", label: "Action Log" },
];

export default function Admin() {
  const [overview, setOverview] = useState(null);
  const [reports, setReports] = useState([]);
  const [log, setLog] = useState([]);
  const [activeTab, setActiveTab] = useState("overview");

  const refresh = useCallback(async () => {
    const [ov, rp, lg] = await Promise.all([api.overview(), api.listReports(), api.actionLog()]);
    setOverview(ov);
    setReports(rp);
    setLog(lg);
  }, []);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, POLL_MS);
    return () => clearInterval(interval);
  }, [refresh]);

  return (
    <div className="admin-page">
      <h2>Municipal Corporation Dashboard</h2>
      <div className="admin-tabs-wrap">
        <Tabs tabs={TABS} active={activeTab} onChange={setActiveTab} />
        <div className="tab-content">
          {activeTab === "overview" && <AdminOverview overview={overview} onRefresh={refresh} />}
          {activeTab === "reports" && <ReportsTable reports={reports} onRefresh={refresh} />}
          {activeTab === "log" && <ActionLog log={log} onRefresh={refresh} />}
        </div>
      </div>
    </div>
  );
}
