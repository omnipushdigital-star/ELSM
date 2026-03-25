import { useMemo } from 'react';

const STATUS_COLOR = {
  New:         'var(--blue)',
  Pending:     'var(--amber)',
  Approved:    'var(--teal)',
  Assigned:    'var(--navy)',
  'In Progress':'var(--amber)',
  Completed:   'var(--green)',
  Breach:      'var(--red)',
  Rejected:    'var(--red)',
};

export default function Dashboard({ user, tickets }) {
  // ── Scope tickets to user's jurisdiction ────────────────────────────────
  const scoped = useMemo(() => {
    const arr = Array.isArray(tickets) ? tickets : [];
    if (!user || user.zone === 'All Zones') return arr;
    if (user.comm) return arr.filter(t =>
      t.zone === user.zone &&
      (t.commissionerate === user.comm || t.city === user.comm)
    );
    return arr.filter(t => t.zone === user.zone);
  }, [tickets, user]);

  const inProgress = scoped.filter(t =>
    ['New','Pending','Approved','Assigned','In Progress'].includes(t.status)
  );

  // ── KPI values ──────────────────────────────────────────────────────────
  const kpis = [
    {
      label: 'Total Machines Declared',
      value: 247,
      sub: '189 Running · 58 Stopped',
      change: '+12 this month',
      up: true,
      accent: 'var(--navy)',
    },
    {
      label: 'Locked Machines',
      value: 198,
      sub: '172 Online · 26 Offline',
      change: '+8 this month',
      up: true,
      accent: 'var(--blue)',
    },
    {
      label: 'Lock Requests In Process',
      value: inProgress.length,
      sub: `${inProgress.filter(t=>t.status==='New'||t.status==='Pending').length} New/Pending · ${inProgress.filter(t=>t.status==='Assigned'||t.status==='In Progress').length} Assigned`,
      change: null,
      accent: 'var(--amber)',
    },
    {
      label: 'Security Alerts',
      value: 3,
      sub: '2 Tamper · 1 Geo-fence',
      change: '-1 from yesterday',
      up: true,
      accent: 'var(--red)',
    },
  ];

  // ── Active tickets (non-completed, non-rejected) ────────────────────────
  const activeTickets = scoped
    .filter(t => !['Completed','Rejected'].includes(t.status))
    .slice(0, 10);

  return (
    <div>
      {/* Header */}
      <div className="page-header">
        <div className="page-title">Dashboard</div>
        <div className="page-subtitle">
          {user?.zone === 'All Zones'
            ? 'PAN India — All Zones'
            : [user?.zone, user?.comm, user?.range].filter(Boolean).join(' · ')}
        </div>
      </div>

      {/* KPI Grid */}
      <div className="kpi-grid">
        {kpis.map(k => (
          <div key={k.label} className="kpi" style={{ '--kpi-accent': k.accent }}>
            <div className="kpi-label">{k.label}</div>
            <div className="kpi-value">{k.value}</div>
            <div className="kpi-sub">{k.sub}</div>
            {k.change && (
              <div className={`kpi-change ${k.up ? 'up' : 'dn'}`}>
                {k.up ? '↑' : '↓'} {k.change}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Alert strip */}
      <div className="alert-strip">
        <div className="alert-item tamper">🔓 Tamper Alert — M-DEL-014, Delhi East</div>
        <div className="alert-item tamper">🔓 Tamper Alert — M-MUM-047, Mumbai West</div>
        <div className="alert-item geo">📍 Geo-fence Breach — M-HYD-033, Hyderabad I</div>
      </div>

      {/* Active tickets */}
      <div className="card">
        <div className="card-title">
          Active Tickets in Jurisdiction
          <span style={{ float: 'right', fontWeight: 400, textTransform: 'none', fontSize: 11 }}>
            {activeTickets.length} of {scoped.filter(t => !['Completed','Rejected'].includes(t.status)).length}
          </span>
        </div>

        {activeTickets.length === 0 ? (
          <div style={{ color: 'var(--text3)', fontSize: 12, padding: '12px 0' }}>
            No active tickets in your jurisdiction.
          </div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Ticket ID</th>
                  <th>Type</th>
                  <th>Machine</th>
                  <th>Firm</th>
                  <th>Jurisdiction</th>
                  <th>Priority</th>
                  <th>Status</th>
                  <th>SLA Deadline</th>
                </tr>
              </thead>
              <tbody>
                {activeTickets.map(t => (
                  <tr key={t.id}>
                    <td><span className="chip">{t.id}</span></td>
                    <td>
                      <span style={{
                        fontSize: 10, padding: '1px 6px', borderRadius: 3,
                        background: t.type==='ESE' ? 'var(--navy-light)' : 'var(--amber-light)',
                        color:      t.type==='ESE' ? 'var(--navy)'       : 'var(--saffron)',
                        fontWeight: 700,
                      }}>{t.type}</span>
                    </td>
                    <td style={{ fontFamily: 'var(--mono)', fontSize: 11 }}>{t.machine}</td>
                    <td style={{ fontSize: 11.5, maxWidth: 160, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{t.firm}</td>
                    <td style={{ fontSize: 11 }}>{t.range}, {t.commissionerate}</td>
                    <td style={{ fontSize: 11, fontWeight: 700, color:
                      t.priority === 'Critical' ? 'var(--red)' :
                      t.priority === 'Urgent'   ? 'var(--saffron)' :
                      t.priority === 'High'     ? 'var(--amber)' : 'var(--text3)'
                    }}>{t.priority}</td>
                    <td>
                      <span className="pill" style={{
                        background: (STATUS_COLOR[t.status] || 'var(--navy)') + '22',
                        color: STATUS_COLOR[t.status] || 'var(--navy)',
                      }}>{t.status}</span>
                    </td>
                    <td style={{ fontFamily: 'var(--mono)', fontSize: 11, color: t.status === 'Breach' ? 'var(--red)' : 'var(--text3)' }}>
                      {t.slaDeadline}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Machines in jurisdiction (static summary) */}
      <div className="grid-2">
        <div className="card">
          <div className="card-title">Machines by Zone</div>
          <table>
            <thead><tr><th>Zone</th><th>Total</th><th>Locked</th><th>Alerts</th></tr></thead>
            <tbody>
              {[
                ['Delhi Zone',      82, 68, 2],
                ['Mumbai Zone',     61, 51, 1],
                ['Hyderabad Zone',  38, 31, 0],
                ['Chennai Zone',    29, 24, 0],
                ['Kolkata Zone',    22, 14, 0],
                ['Bengaluru Zone',  10,  7, 0],
                ['Ahmedabad Zone',   5,  3, 0],
              ]
              .filter(([zone]) => user?.zone === 'All Zones' || zone === user?.zone)
              .map(([zone, total, locked, alerts]) => (
                <tr key={zone}>
                  <td>{zone}</td>
                  <td style={{ fontWeight: 700 }}>{total}</td>
                  <td style={{ color: 'var(--blue)', fontWeight: 600 }}>{locked}</td>
                  <td style={{ color: alerts > 0 ? 'var(--red)' : 'var(--text3)', fontWeight: alerts > 0 ? 700 : 400 }}>
                    {alerts > 0 ? '⚠️ ' + alerts : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="card">
          <div className="card-title">Ticket Summary</div>
          <table>
            <thead><tr><th>Status</th><th>ESE</th><th>EUE</th><th>Total</th></tr></thead>
            <tbody>
              {['New','Pending','Approved','Assigned','In Progress','Completed','Breach'].map(st => {
                const ese = scoped.filter(t => t.status === st && t.type === 'ESE').length;
                const eue = scoped.filter(t => t.status === st && t.type === 'EUE').length;
                if (!ese && !eue) return null;
                return (
                  <tr key={st}>
                    <td>
                      <span className="pill" style={{
                        background: (STATUS_COLOR[st] || 'var(--navy)') + '22',
                        color: STATUS_COLOR[st] || 'var(--navy)',
                      }}>{st}</span>
                    </td>
                    <td>{ese || '—'}</td>
                    <td>{eue || '—'}</td>
                    <td style={{ fontWeight: 700 }}>{ese + eue}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
