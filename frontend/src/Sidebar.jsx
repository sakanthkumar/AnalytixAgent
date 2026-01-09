import React from 'react';

const Sidebar = ({ activeTab, onTabChange }) => {
    const menuItems = [
        { id: 'dashboard', label: 'Dashboard', icon: '📊' },
        { id: 'analysis', label: 'New Analysis', icon: '🔍' },
        { id: 'logs', label: 'Data Logs', icon: '📁' },
        { id: 'reports', label: 'History & Reports', icon: '🕰️' },
        { id: 'manuals', label: 'Knowledge Base', icon: '📚' },
        { id: 'settings', label: 'Settings', icon: '⚙️' },
    ];

    return (
        <aside className="sidebar">
            <div style={{ padding: '0 0.5rem 2rem', fontWeight: 'bold', fontSize: '1.25rem', color: 'var(--primary-color)' }}>
                🏭 Maintain.AI
            </div>
            <nav>
                {menuItems.map(item => (
                    <div
                        key={item.id}
                        className={`nav-item ${activeTab === item.id ? 'active' : ''}`}
                        onClick={() => onTabChange(item.id)}
                    >
                        <span>{item.icon}</span>
                        <span>{item.label}</span>
                    </div>
                ))}
            </nav>

            <div style={{ marginTop: 'auto', padding: '1rem', borderTop: '1px solid var(--border-color)' }}>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    System Status: <span style={{ color: '#10b981' }}>● Online</span>
                </div>
            </div>
        </aside>
    );
};
export default Sidebar;
