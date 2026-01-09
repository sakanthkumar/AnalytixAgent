import React from 'react';
import { useTheme } from './ThemeContext';

const Header = ({ title }) => {
    const { theme, toggleTheme } = useTheme();

    return (
        <header className="top-bar">
            <h2>{title}</h2>
            <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                <button className="icon-btn" onClick={toggleTheme} title="Toggle Theme">
                    {theme === 'dark' ? '☀️ Light Mode' : '🌙 Dark Mode'}
                </button>
            </div>
        </header>
    );
};
export default Header;
