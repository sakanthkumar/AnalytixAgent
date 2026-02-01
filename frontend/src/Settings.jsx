import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useTheme } from './ThemeContext';

export default function Settings() {
    const { theme, toggleTheme } = useTheme();
    const isDark = theme === 'dark';
    const [models, setModels] = useState([]);
    const [currentModel, setCurrentModel] = useState('');
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState('');

    // New Settings State
    const [autoAnalyze, setAutoAnalyze] = useState(() => localStorage.getItem('autoAnalyze') !== 'false');
    const [notifications, setNotifications] = useState(() => localStorage.getItem('notifications') === 'true');
    const [temperature, setTemperature] = useState(0.1);

    // Expert State
    const [showExpert, setShowExpert] = useState(false);
    const [ragDepth, setRagDepth] = useState(2);
    const [systemPrompt, setSystemPrompt] = useState("");
    const [ollamaUrl, setOllamaUrl] = useState("");

    useEffect(() => {
        fetchConfig();
        fetchModels();
    }, []);

    // Persist new settings
    useEffect(() => { localStorage.setItem('autoAnalyze', autoAnalyze); }, [autoAnalyze]);
    useEffect(() => { localStorage.setItem('notifications', notifications); }, [notifications]);

    const fetchConfig = async () => {
        try {
            const res = await axios.get("http://localhost:8000/settings/config");
            setCurrentModel(res.data.model);
            if (res.data.temperature !== undefined) setTemperature(res.data.temperature);
            if (res.data.rag_depth !== undefined) setRagDepth(res.data.rag_depth);
            if (res.data.system_prompt) setSystemPrompt(res.data.system_prompt);
            if (res.data.ollama_url) setOllamaUrl(res.data.ollama_url);
        } catch (e) {
            console.error("Failed to fetch config", e);
        }
    };

    const fetchModels = async () => {
        try {
            const res = await axios.get("http://localhost:8000/settings/models");
            setModels(res.data.models || []);
        } catch (e) {
            console.error("Failed to fetch models", e);
        }
    };

    const handleModelChange = async (e) => {
        const newModel = e.target.value;
        setLoading(true);
        setMessage('');
        try {
            await axios.post("http://localhost:8000/settings/model", { model: newModel });
            setCurrentModel(newModel);
            setMessage(`Successfully switched to ${newModel}`);
        } catch (e) {
            setMessage("Error switching model.");
        } finally {
            setLoading(false);
        }
    };

    const handleTempChange = async (e) => {
        const val = parseFloat(e.target.value);
        setTemperature(val);
        try {
            await axios.post("http://localhost:8000/settings/temperature", { temperature: val });
        } catch (e) { console.error("Failed to set temp", e); }
    };

    const handleClearKB = async () => {
        if (!window.confirm("Are you sure? This will delete all analyzed manuals.")) return;
        try {
            await axios.post("http://localhost:8000/manuals/clear");
            alert("Knowledge Base cleared.");
        } catch (e) { alert("Failed to clear KB."); }
    };

    const saveExpertSettings = async () => {
        try {
            await axios.post("http://localhost:8000/settings/expert", { system_prompt: systemPrompt, ollama_url: ollamaUrl });
            await axios.post("http://localhost:8000/settings/rag", { n_results: ragDepth });
            alert("Expert settings saved!");
        } catch (e) { alert("Failed to save expert settings."); }
    };

    return (
        <div className="section-box" style={{ maxWidth: '800px', margin: '0 auto' }}>
            <h2>⚙️ Settings</h2>

            <div className="card" style={{ marginTop: '20px' }}>
                <h3>🤖 AI Configuration</h3>
                <p>Select the Large Language Model (LLM) to drive the analysis agent.</p>

                <div style={{ marginTop: '15px' }}>
                    <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Active Model</label>
                    <select
                        value={currentModel}
                        onChange={handleModelChange}
                        disabled={loading}
                        style={{
                            padding: '10px',
                            borderRadius: '5px',
                            width: '100%',
                            maxWidth: '400px',
                            border: '1px solid var(--border-color)',
                            backgroundColor: 'var(--bg-secondary)',
                            color: 'var(--text-primary)'
                        }}
                    >
                        {models.length === 0 && <option value={currentModel}>{currentModel} (Current)</option>}
                        {models.map(m => <option key={m} value={m}>{m}</option>)}
                    </select>
                </div>

                {loading && <p style={{ color: 'var(--accent-color)', marginTop: '10px' }}>Switching model...</p>}
                {message && <p style={{ color: 'var(--success-color)', marginTop: '10px' }}>{message}</p>}
            </div>

            <div className="card" style={{ marginTop: '20px' }}>
                <h3>🧠 Advanced Intelligence</h3>

                <div style={{ marginBottom: '15px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
                        <strong>Creativity (Temperature): {temperature}</strong>
                        <span>{temperature <= 0.3 ? "Precise" : temperature >= 0.7 ? "Creative" : "Balanced"}</span>
                    </div>
                    <input
                        type="range"
                        min="0" max="1" step="0.1"
                        value={temperature}
                        onChange={handleTempChange}
                        style={{ width: '100%', accentColor: 'var(--accent-color)' }}
                    />
                    <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '5px' }}>
                        Lower values (0.1) are better for code/math. Higher values (0.7+) make explanations more varied.
                    </p>
                </div>

                <div style={{ marginTop: '20px', paddingTop: '20px', borderTop: '1px solid var(--border-color)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <div>
                            <strong>Clear Knowledge Base</strong>
                            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Delete all ingested manuals and reset the RAG index.</p>
                        </div>
                        <button
                            className="secondary-btn"
                            onClick={handleClearKB}
                            style={{ borderColor: 'var(--danger-color)', color: 'var(--danger-color)' }}
                        >
                            🗑️ Clear Index
                        </button>
                    </div>
                </div>
            </div>

            <div className="card" style={{ marginTop: '20px', border: '1px solid var(--accent-color)' }}>
                <div
                    style={{ display: 'flex', justifyContent: 'space-between', cursor: 'pointer' }}
                    onClick={() => setShowExpert(!showExpert)}
                >
                    <h3>🛠️ Expert Mode {showExpert ? '▼' : '▶'}</h3>
                </div>

                {showExpert && (
                    <div style={{ marginTop: '15px' }}>
                        <div style={{ marginBottom: '15px' }}>
                            <label><strong>RAG Context Depth (Chunks): {ragDepth}</strong></label>
                            <input
                                type="range" min="1" max="10"
                                value={ragDepth}
                                onChange={(e) => setRagDepth(parseInt(e.target.value))}
                                style={{ width: '100%' }}
                            />
                            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>How many manual values to read? More = Slower but smarter.</p>
                        </div>

                        <div style={{ marginBottom: '15px' }}>
                            <label><strong>System Prompt (Persona)</strong></label>
                            <textarea
                                value={systemPrompt}
                                onChange={(e) => setSystemPrompt(e.target.value)}
                                rows={6}
                                style={{ width: '100%', padding: '10px', backgroundColor: 'var(--bg-primary)', color: 'var(--text-primary)', border: '1px solid var(--border-color)', borderRadius: '4px' }}
                            />
                        </div>

                        <div style={{ marginBottom: '15px' }}>
                            <label><strong>Ollama Host URL</strong></label>
                            <input
                                type="text"
                                value={ollamaUrl}
                                onChange={(e) => setOllamaUrl(e.target.value)}
                                style={{ width: '100%', padding: '8px', backgroundColor: 'var(--bg-primary)', color: 'var(--text-primary)', border: '1px solid var(--border-color)', borderRadius: '4px' }}
                            />
                        </div>

                        <button className="primary-btn" onClick={saveExpertSettings}>💾 Save Expert Config</button>
                    </div>
                )}
            </div>

            <div className="card" style={{ marginTop: '20px' }}>
                <h3>🎨 Appearance & Preferences</h3>

                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '15px' }}>
                    <div>
                        <strong>Dark Mode</strong>
                        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Toggle application theme</p>
                    </div>
                    <button
                        onClick={toggleTheme}
                        className={isDark ? "secondary-btn" : "primary-btn"}
                        style={{ minWidth: '100px' }}
                    >
                        {isDark ? "☀️ Light" : "🌙 Dark"}
                    </button>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '15px' }}>
                    <div>
                        <strong>Auto-Analyze Uploads</strong>
                        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Automatically run "Identify Failures" on new CSVs</p>
                    </div>
                    <label className="switch">
                        <input type="checkbox" checked={autoAnalyze} onChange={(e) => setAutoAnalyze(e.target.checked)} />
                        <span className="slider round"></span>
                    </label>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div>
                        <strong>Analysis Notifications</strong>
                        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Play sound when long-running analysis completes</p>
                    </div>
                    <label className="switch">
                        <input type="checkbox" checked={notifications} onChange={(e) => setNotifications(e.target.checked)} />
                        <span className="slider round"></span>
                    </label>
                </div>
            </div>

            <div className="card" style={{ marginTop: '20px', borderColor: 'var(--danger-color)' }}>
                <h3 style={{ color: 'var(--danger-color)' }}>⚠️ Data Management</h3>
                <p>Clear all uploaded data and analysis history from the current session.</p>
                <button
                    className="secondary-btn"
                    onClick={() => window.location.reload()}
                    style={{ borderColor: 'var(--danger-color)', color: 'var(--danger-color)', marginTop: '10px' }}
                >
                    Reset Session
                </button>
            </div>

            <style>{`
        .switch { position: relative; display: inline-block; width: 50px; height: 24px; }
        .switch input { opacity: 0; width: 0; height: 0; }
        .slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: #ccc; transition: .4s; border-radius: 24px; }
        .slider:before { position: absolute; content: ""; height: 18px; width: 18px; left: 3px; bottom: 3px; background-color: white; transition: .4s; border-radius: 50%; }
        input:checked + .slider { background-color: var(--accent-color); }
        input:checked + .slider:before { transform: translateX(26px); }
      `}</style>
        </div>
    );
}
