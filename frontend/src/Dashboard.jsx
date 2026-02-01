import { useEffect, useState } from "react";
import axios from "axios";
import Upload from "./Upload";
import Chat from "./Chat";
import DataGrid from "./DataGrid";
import Manuals from "./Manuals";
import Sidebar from "./Sidebar";
import Header from "./Header";
import Reports from './Reports';
import Settings from './Settings';
import "./App.css";

// Markdown Renderer
const ReportView = ({ text }) => {
  if (!text) return null;
  return (
    <div className="report-content">
      {text.split('\n').map((line, i) => {
        if (line.startsWith('###')) return <h4 key={i}>{line.replace('###', '')}</h4>;
        if (line.startsWith('**')) return <strong key={i} style={{ display: 'block', marginTop: '10px' }}>{line.replace(/\*\*/g, '')}</strong>;
        return <p key={i} style={{ marginBottom: '5px' }}>{line}</p>;
      })}
    </div>
  );
};

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [plots, setPlots] = useState(null);
  const [reports, setReports] = useState({});
  const [reportLoading, setReportLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [showFailures, setShowFailures] = useState(false);
  const [failures, setFailures] = useState([]);

  const loadFailures = async () => {
    try {
      const res = await axios.get("http://localhost:8000/failures");
      if (res.data.failures) {
        setFailures(res.data.failures);
        setShowFailures(true);
        // Auto-save report for history
        await axios.post("http://localhost:8000/reports/save", { analysis_type: "Failure Scan" });
      } else {
        alert("No failures detected in the dataset!");
      }
    } catch (e) { console.error(e); }
  };


  const [showAcronymModal, setShowAcronymModal] = useState(false);
  const [unknownAcronyms, setUnknownAcronyms] = useState([]);
  const [acronymInputs, setAcronymInputs] = useState({});



  const startAnalysis = async () => {
    try {
      await axios.post("http://localhost:8000/analysis/start");
      // Optional: Add toast "Analysis Started"
      console.log("Analysis started in background");
    } catch (e) {
      console.error("Failed to start analysis", e);
    }
  };

  const handleUploadSuccess = (uploadData) => {
    fetchEDA();
    setActiveTab('dashboard');

    if (uploadData && uploadData.unknown_acronyms && uploadData.unknown_acronyms.length > 0) {
      setUnknownAcronyms(uploadData.unknown_acronyms);
      setShowAcronymModal(true);
    } else {
      // No missing definitions, start immediately
      startAnalysis();
    }
  };

  const handleAcronymSubmit = async () => {
    try {
      await axios.post("http://localhost:8000/settings/acronyms", { acronyms: acronymInputs });
      setShowAcronymModal(false);
      alert("Definitions saved! Analysis starting...");
      startAnalysis();
    } catch (e) { alert("Failed to save definitions"); }
  };

  const handleAcronymSkip = () => {
    setShowAcronymModal(false);
    startAnalysis();
  };

  // Data Fetching
  const fetchEDA = async () => {
    setReportLoading(false); // No auto-loading
    try {
      const [edaRes, plotsRes] = await Promise.all([
        axios.get("http://localhost:8000/eda"),
        axios.get("http://localhost:8000/eda_plots")
      ]);

      if (edaRes.data.error) setData(null);
      else {
        setData(edaRes.data);
        // We do NOT check checkAcronyms() here anymore, because upload handler does it.
        // checkAcronyms(); 
      }

      if (!plotsRes.data.error) setPlots(plotsRes.data);
    } catch (e) {
      console.error(e);
    }
  };

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { fetchEDA(); }, []);

  // Manual Analysis Handler
  const runAnalysis = async (type) => {
    setReportLoading(true);
    // Don't clear previous reports, just add/update

    try {
      if (type === 'what') {
        // ULTRA-FAST PATH: Use deterministic Python analysis
        const res = await axios.get("http://localhost:8000/analysis/fast_failure");
        if (res.data.answer) {
          setReports(prev => ({ ...prev, 'Failure Identification': res.data.answer }));
        }
        loadFailures(); // Auto-open logs
      } else {
        // CACHED PATH: Fetch pre-computed analysis
        const res = await axios.get(`http://localhost:8000/analysis/report?type=${type}`);

        const titles = { why: "AI Reliability Report", impact: "AI Reliability Report", fix: "AI Reliability Report" };
        const title = titles[type] || "Analysis Report";

        if (res.data.answer) {
          setReports(prev => ({ ...prev, [title]: res.data.answer }));
        }
      }
    } catch (e) {
      alert("Analysis failed. Please check backend connection.");
    } finally {
      setReportLoading(false);
    }
  };

  // View Components
  const renderDashboard = () => {
    // State lifted to parent

    if (!data) return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
        <div className="upload-area">
          <h3>Start New Analysis</h3>
          <p>Upload your machine logs (CSV) to begin diagnosis.</p>
          <Upload onUploadSuccess={handleUploadSuccess} />
        </div>
      </div>
    );

    return (
      <div className="app-content-grid" style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) 350px', gap: '1.5rem', height: '100%' }}>
        <div className="scrollable-content" style={{ overflowY: 'auto', paddingRight: '1rem' }}>

          {/* Analysis Control Panel - New Feature */}
          <section className="section-box">
            <h3>🛠️ Analysis Control Panel</h3>
            <p style={{ marginBottom: '1rem' }}>Select an analysis module to execute:</p>
            <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
              <button className="primary-btn" onClick={() => runAnalysis('what')}>🔍 Identify Failures</button>
              <button className="secondary-btn" onClick={loadFailures} style={{ borderColor: 'var(--danger-color)', color: 'var(--danger-color)' }}>📋 View Failure Log</button>
              <button className="primary-btn" style={{ backgroundColor: 'var(--accent-color)', width: '100%' }} onClick={() => runAnalysis('why')}>🧠 Generate AI Reliability Report</button>
            </div>
          </section>

          {/* Acronym Definition Modal */}
          {showAcronymModal && (
            <div className="modal-overlay">
              <div className="modal-content" style={{ maxWidth: '600px' }}>
                <header className="modal-header">
                  <h2 style={{ color: 'var(--primary-color)' }}>🧠 Define Failure Modes</h2>
                  <button className="close-btn" onClick={handleAcronymSkip}>Skip</button>
                </header>
                <div style={{ padding: '1rem 0' }}>
                  <p>The system detected undefined acronyms by the backend. Please identify them for accurate analysis.</p>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginTop: '1rem' }}>
                    {unknownAcronyms.map(acronym => (
                      <div key={acronym} style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <strong style={{ minWidth: '60px' }}>{acronym}:</strong>
                        <input
                          type="text"
                          placeholder={`Meaning of ${acronym}...`}
                          value={acronymInputs[acronym] || ''}
                          style={{ flex: 1, padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }}
                          onChange={(e) => setAcronymInputs(prev => ({ ...prev, [acronym]: e.target.value }))}
                        />
                      </div>
                    ))}
                  </div>
                </div>
                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '1rem' }}>
                  <button className="secondary-btn" onClick={handleAcronymSkip}>Skip Definitions</button>
                  <button className="primary-btn" onClick={handleAcronymSubmit}>Save & Improve Analysis</button>
                </div>
              </div>
            </div>
          )}

          {/* Failure List Modal */}
          {showFailures && (
            <div className="modal-overlay">
              <div className="modal-content" style={{ maxWidth: '900px' }}>
                <header className="modal-header">
                  <h2 style={{ color: 'var(--danger-color)' }}>⚠️ Failure Log ({failures.length})</h2>
                  <button className="close-btn" onClick={() => setShowFailures(false)}>Close</button>
                </header>
                <div className="table-wrapper" style={{ maxHeight: '400px', overflowY: 'auto' }}>
                  <table>
                    <thead>
                      <tr>
                        {failures.length > 0 && Object.keys(failures[0]).map(k => <th key={k}>{k}</th>)}
                      </tr>
                    </thead>
                    <tbody>
                      {failures.map((row, i) => (
                        <tr key={i}>
                          {Object.values(row).map((v, j) => <td key={j}>{v}</td>)}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <p style={{ textAlign: 'right', fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '1rem' }}>
                  Report automatically saved to history.
                </p>
              </div>
            </div>
          )}

          {/* Report Section */}
          <section className="section-box" style={{ borderLeft: '4px solid var(--accent-color)', minHeight: '100px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3>📝 AI Reliability Report</h3>
              {reportLoading && <span className="spinner-small"></span>}
            </div>

            {Object.keys(reports).length === 0 && !reportLoading && (
              <p style={{ fontStyle: 'italic', color: 'var(--text-muted)' }}>Select a module above to generate a report.</p>
            )}

            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              {Object.entries(reports).map(([title, content]) => (
                <div key={title} className="report-card fade-in" style={{ backgroundColor: 'var(--bg-primary)', padding: '15px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                  <h4 style={{ borderBottom: '1px solid var(--border-color)', paddingBottom: '10px', marginBottom: '10px', color: 'var(--primary-color)' }}>{title}</h4>
                  <ReportView text={content} />
                </div>
              ))}
            </div>
          </section>

          {/* KPI Cards */}
          <section className="cards-grid">
            <div className="card"><h3>Total Failures</h3><p style={{ fontSize: '2rem', fontWeight: 'bold' }}>{data.failure_count ?? data.shape[0]}</p></div>
            <div className="card"><h3>Failure Rate</h3><p style={{ fontSize: '2rem', fontWeight: 'bold' }}>{data.failure_rate}%</p></div>
            <div className="card"><h3>Missing Data</h3><p style={{ fontSize: '2rem', fontWeight: 'bold' }}>{Object.values(data.missing_values).reduce((a, b) => a + b, 0)}</p></div>
          </section>

          {/* Charts */}
          {plots && (
            <section className="cards-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))' }}>
              {plots.heatmap && (
                <div className="card">
                  <h4>Correlation Matrix</h4>
                  <img src={`data:image/png;base64,${plots.heatmap}`} style={{ width: '100%', borderRadius: '4px' }} alt="Heatmap" />
                </div>
              )}
              {Object.keys(plots).filter(k => k.startsWith('dist_')).map(k => (
                <div key={k} className="card">
                  <h4>{k.replace('dist_', '')} Distribution</h4>
                  <img src={`data:image/png;base64,${plots[k]}`} style={{ width: '100%', borderRadius: '4px' }} alt={k} />
                </div>
              ))}
            </section>
          )}
        </div>

        {/* Chat Sidebar */}
        <div className="chat-panel" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
          <Chat />
        </div>
      </div>
    );
  };

  return (
    <div className="app-layout">
      <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />
      <div className="main-content-area">
        <Header title={activeTab.charAt(0).toUpperCase() + activeTab.slice(1)} />
        <main className="scrollable-content">
          {activeTab === 'dashboard' && renderDashboard()}
          {activeTab === 'analysis' && (
            <div className="container" style={{ maxWidth: '600px', margin: '0 auto' }}>
              <h2>New Analysis</h2>
              <div className="card">
                <p>Upload a new dataset to reset the dashboard.</p>
                <Upload onUploadSuccess={() => { setData(null); fetchEDA(); setActiveTab('dashboard'); }} />
              </div>
            </div>
          )}
          {activeTab === 'logs' && data && <DataGrid />}
          {activeTab === 'logs' && !data && <p style={{ textAlign: 'center', marginTop: '3rem' }}>No data available.</p>}
          {activeTab === 'reports' && <Reports />}
          {activeTab === 'manuals' && <Manuals />}
          {activeTab === 'settings' && <Settings />}
        </main>
      </div>
    </div>
  );
}
