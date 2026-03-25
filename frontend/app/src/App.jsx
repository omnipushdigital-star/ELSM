import { useState, useEffect } from 'react';
import './styles/globals.css';
import { INITIAL_TICKETS } from './data/gstMaster';
import Login       from './components/Login';
import Layout      from './components/Layout';
import Dashboard   from './components/Dashboard';
import DGGITickets from './components/DGGITickets';

// ── Placeholder pages (build these out incrementally) ──────────────────────
function PlaceholderPage({ title, icon }) {
  return (
    <div>
      <div className="page-header">
        <div className="page-title">{icon} {title}</div>
        <div className="page-subtitle">This module is under development</div>
      </div>
      <div className="card" style={{ textAlign: 'center', padding: '40px', color: 'var(--text3)' }}>
        <div style={{ fontSize: 40, marginBottom: 12 }}>{icon}</div>
        <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--navy)' }}>{title}</div>
        <div style={{ fontSize: 12, marginTop: 6 }}>Coming soon in the next sprint.</div>
      </div>
    </div>
  );
}

// ── Ticket state: load from localStorage, persist on change ───────────────
function loadTickets() {
  try {
    const s = localStorage.getItem('elsm_tickets_v2');
    if (s) {
      const parsed = JSON.parse(s);
      if (Array.isArray(parsed) && parsed.length > 0) return parsed;
    }
  } catch (_) {}
  return INITIAL_TICKETS;
}

// ── App root ──────────────────────────────────────────────────────────────
export default function App() {
  const [user,    setUser]    = useState(() => {
    try {
      const s = localStorage.getItem('elsm_user');
      return s ? JSON.parse(s) : null;
    } catch(_) { return null; }
  });

  const [page,    setPage]    = useState('dashboard');
  const [tickets, setTickets] = useState(loadTickets);

  // Persist tickets to localStorage whenever they change
  useEffect(() => {
    try { localStorage.setItem('elsm_tickets_v2', JSON.stringify(tickets)); }
    catch(_) {}
  }, [tickets]);

  // Not logged in → show login screen
  if (!user) {
    return <Login onLogin={u => { setUser(u); setPage('dashboard'); }} />;
  }

  // Render the active page
  function renderPage() {
    switch (page) {
      case 'dashboard': return <Dashboard user={user} tickets={tickets} />;
      case 'dggi':      return <DGGITickets user={user} tickets={tickets} setTickets={setTickets} />;
      case 'locks':     return <PlaceholderPage icon="📦" title="Lock Inventory" />;
      case 'events':    return <PlaceholderPage icon="📋" title="ESE / EUE Events" />;
      case 'alerts':    return <PlaceholderPage icon="🚨" title="Alerts & Notices" />;
      case 'map':       return <PlaceholderPage icon="🗺️" title="Zone Coverage" />;
      case 'sla':       return <PlaceholderPage icon="📊" title="SLA & Reports" />;
      case 'gst':       return <PlaceholderPage icon="🏢" title="GST Master Data" />;
      case 'billing':   return <PlaceholderPage icon="💰" title="Billing & Invoicing" />;
      case 'settings':  return <PlaceholderPage icon="⚙️"  title="Settings" />;
      default:          return <Dashboard user={user} tickets={tickets} />;
    }
  }

  return (
    <Layout user={user} page={page} setPage={setPage}>
      {renderPage()}
    </Layout>
  );
}
