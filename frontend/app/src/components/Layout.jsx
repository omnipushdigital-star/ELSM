const ROLE_LABELS = {
  super_admin:     'Super Admin',
  cbic_admin:      'CBIC Admin',
  nodal_officer:   'Range Officer',
  auditor:         'Auditor (Read-only)',
  bsnl_admin:      'BSNL Admin',
  bsnl_supervisor: 'BSNL Supervisor',
  field_engineer:  'Field Engineer',
};

const NAV = [
  { key: 'dashboard', icon: '🏠', label: 'Dashboard',        section: 'main' },
  { key: 'dggi',      icon: '🔒', label: 'DGGI Seal Tickets', section: 'main' },
  { key: 'locks',     icon: '📦', label: 'Lock Inventory',    section: 'main' },
  { key: 'events',    icon: '📋', label: 'ESE / EUE Events',  section: 'main' },
  { key: 'alerts',    icon: '🚨', label: 'Alerts & Notices',  section: 'main', badge: 2 },
  { key: 'map',       icon: '🗺️', label: 'Zone Coverage',     section: 'reports' },
  { key: 'sla',       icon: '📊', label: 'SLA & Reports',     section: 'reports' },
  { key: 'gst',       icon: '🏢', label: 'GST Master Data',   section: 'admin' },
  { key: 'billing',   icon: '💰', label: 'Billing & Invoicing', section: 'admin' },
  { key: 'settings',  icon: '⚙️', label: 'Settings',          section: 'admin' },
];

// Which pages each role can access
const ROLE_ACCESS = {
  super_admin:     ['dashboard','dggi','locks','events','alerts','map','sla','gst','billing','settings'],
  cbic_admin:      ['dashboard','dggi','locks','events','alerts','map','sla','gst','settings'],
  nodal_officer:   ['dashboard','dggi','events','alerts'],
  auditor:         ['dashboard','dggi','locks','events','alerts','map','sla'],
  bsnl_admin:      ['dashboard','dggi','locks','events','alerts','map','sla','billing','settings'],
  bsnl_supervisor: ['dashboard','dggi','locks','events','alerts'],
  field_engineer:  ['dashboard','dggi','events'],
};

export default function Layout({ user, page, setPage, children }) {
  const allowed = ROLE_ACCESS[user.role] || [];
  const sections = ['main', 'reports', 'admin'];
  const sectionLabels = { main: 'Main', reports: 'Reports', admin: 'Admin' };

  const initials = user.name.split(' ').map(w => w[0]).slice(0,2).join('');

  return (
    <div className="app-shell">
      {/* ── SIDEBAR ── */}
      <div className="sidebar">
        <div className="sidebar-brand">
          <div className="brand-title">⚙️ ELSM</div>
          <div className="brand-sub">CBIC · Lock Management</div>
        </div>

        <div style={{ flex: 1, overflowY: 'auto' }}>
          {sections.map(sec => {
            const items = NAV.filter(n => n.section === sec && allowed.includes(n.key));
            if (!items.length) return null;
            return (
              <div key={sec} className="sidebar-section">
                <div className="sidebar-label">{sectionLabels[sec]}</div>
                {items.map(item => (
                  <div key={item.key}
                    className={`nav-item ${page === item.key ? 'active' : ''}`}
                    onClick={() => setPage(item.key)}
                  >
                    <span className="nav-icon">{item.icon}</span>
                    <span>{item.label}</span>
                    {item.badge ? <span className="nav-badge">{item.badge}</span> : null}
                  </div>
                ))}
              </div>
            );
          })}
        </div>

        {/* Jurisdiction badge at bottom */}
        <div style={{ padding: '10px 14px 14px', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
          <div style={{ fontSize: 9.5, color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 4 }}>Jurisdiction</div>
          <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.75)', lineHeight: 1.6 }}>
            {user.zone === 'All Zones' ? 'PAN India — All Zones' : user.zone}
            {user.comm  && <><br />{user.comm}</>}
            {user.range && <><br />{user.range}</>}
          </div>
        </div>
      </div>

      {/* ── MAIN AREA ── */}
      <div className="main-area">
        {/* Topbar */}
        <div className="topbar">
          <div className="topbar-left">
            <div>
              <div className="topbar-title">
                {NAV.find(n => n.key === page)?.icon} {NAV.find(n => n.key === page)?.label || 'ELSM Portal'}
              </div>
              <div className="topbar-sub">
                Government of India · CBIC · HSNS Cess Portal
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div className="user-pill">
              <div className="user-avatar">{initials}</div>
              <div>
                <div className="user-name">{user.name}</div>
                <div className="user-role">{ROLE_LABELS[user.role]}</div>
              </div>
            </div>
            <button className="logout-btn" onClick={() => {
              localStorage.removeItem('elsm_user');
              window.location.reload();
            }}>
              ⏏ Logout
            </button>
          </div>
        </div>

        {/* Page content */}
        <div className="content">
          {children}
        </div>
      </div>
    </div>
  );
}
