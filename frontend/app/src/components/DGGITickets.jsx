import { useState, useMemo } from 'react';
import { PREMISES, MACHINES, OFFICERS, ENGINEERS, DIVISIONS, RANGES, ZONES, COMMS } from '../data/gstMaster';

const STATUS_COLOR = {
  New:'var(--blue)', Pending:'var(--amber)', Approved:'var(--teal)',
  Assigned:'var(--navy)', 'In Progress':'var(--amber)',
  Completed:'var(--green)', Breach:'var(--red)', Rejected:'var(--red)',
};
const PRIORITY_COLOR = {
  Normal:'var(--text3)', High:'var(--amber)', Urgent:'var(--saffron)', Critical:'var(--red)',
};

function makeId(tickets) {
  const n = tickets.length + 48;
  return `TKT-2026-${String(n).padStart(4,'0')}`;
}

// ── CREATE TICKET FORM ──────────────────────────────────────────────────────
function CreateForm({ user, onSubmit, onCancel }) {
  const isNodal    = user.role === 'nodal_officer';
  const userZone   = user.zone === 'All Zones' ? ZONES[0] : user.zone;

  const [form, setForm] = useState({
    type:'ESE', priority:'Normal',
    zone:     userZone,
    comm:     user.comm || (COMMS[userZone]?.[0] ?? ''),
    div:      'Division I',
    range:    user.range || 'Range I',
    rangeOfficer: isNodal ? user.name : '',
    firm:'', machine:'', hsnsReg:'', gstin:'', reqRef:'', notes:'',
  });

  const up = (k,v) => setForm(p => ({ ...p, [k]:v }));

  const availZones = user.zone === 'All Zones' ? ZONES : [user.zone];
  const availComms = user.comm ? [user.comm] : (COMMS[form.zone] || []);
  const availRanges = user.range ? [user.range] : RANGES;

  const premises = PREMISES[form.comm] || [];
  const machines = form.firm ? (MACHINES[form.firm] || []) : [];
  const officers = OFFICERS[form.comm] || [];

  const canSubmit = (form.firm || form.machine) && form.hsnsReg && form.gstin;

  function handleSubmit(e) {
    e.preventDefault();
    if (!canSubmit) return;
    onSubmit(form);
  }

  return (
    <div>
      <div className="page-header">
        <div className="breadcrumb">
          <span style={{cursor:'pointer',color:'var(--navy)'}} onClick={onCancel}>Tickets</span>
          <span>/</span> New Ticket
        </div>
        <div className="page-title">
          Create {form.type === 'ESE' ? 'Sealing (ESE)' : 'Unsealing (EUE)'} Ticket
        </div>
        <div className="page-subtitle">
          {form.zone} · {form.comm} · {form.range}
          {isNodal && ` · ${user.name}`}
        </div>
      </div>

      <div className="info-banner">
        <strong>Ref:</strong> HSNS Cess Act 2025 (effective 01.02.2026) · Advisory No. 04/2026 ·
        Form HSNS DEC-01 · Portal: www.cbic-gst.gov.in
      </div>

      <form onSubmit={handleSubmit}>
        <div className="grid-2">
          {/* Left: Request details */}
          <div className="card">
            <div className="card-title">Request Details</div>

            {/* Type toggle */}
            <div className="form-group">
              <label className="form-label">Event Type *</label>
              <div style={{ display:'flex', gap:8 }}>
                {['ESE','EUE'].map(t => (
                  <button key={t} type="button" onClick={() => up('type',t)} style={{
                    flex:1, padding:'10px', borderRadius:4, cursor:'pointer', fontFamily:'var(--font)',
                    fontWeight:700, fontSize:12.5,
                    border:`2px solid ${form.type===t ? 'var(--navy)' : 'var(--border)'}`,
                    background: form.type===t ? 'var(--navy)' : '#fff',
                    color:      form.type===t ? '#fff'        : 'var(--text2)',
                  }}>
                    {t === 'ESE' ? '🔒 Electronic Sealing (ESE)' : '🔓 Electronic Unsealing (EUE)'}
                  </button>
                ))}
              </div>
            </div>

            {/* Priority */}
            <div className="form-group">
              <label className="form-label">Priority</label>
              <div style={{ display:'flex', gap:6 }}>
                {['Normal','High','Urgent','Critical'].map(p => (
                  <button key={p} type="button" onClick={() => up('priority',p)} style={{
                    flex:1, padding:'6px 4px', borderRadius:4, cursor:'pointer',
                    fontFamily:'var(--font)', fontSize:11, fontWeight:700,
                    border:`1.5px solid ${form.priority===p ? PRIORITY_COLOR[p] : 'var(--border)'}`,
                    background: form.priority===p ? 'var(--navy-xlight)' : '#fff',
                    color:      form.priority===p ? PRIORITY_COLOR[p]    : 'var(--text3)',
                  }}>{p}</button>
                ))}
              </div>
            </div>

            {/* HSNS + GSTIN */}
            <div className="form-group" style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:12 }}>
              <div>
                <label className="form-label">HSNS Reg. No. *</label>
                <input className="form-input" style={{fontFamily:'var(--mono)',fontSize:12}}
                  placeholder="CHTPR0365MHS0XXX" value={form.hsnsReg}
                  onChange={e => up('hsnsReg', e.target.value)} required />
              </div>
              <div>
                <label className="form-label">GSTIN *</label>
                <input className="form-input" style={{fontFamily:'var(--mono)',fontSize:12}}
                  placeholder="07AABCS1429B1Z5" value={form.gstin}
                  onChange={e => up('gstin', e.target.value)} required />
              </div>
            </div>

            {/* Premise */}
            <div className="form-group">
              <label className="form-label">Manufacturer / Premise *</label>
              <select className="form-select" value={form.firm}
                onChange={e => { up('firm', e.target.value); up('machine',''); }}>
                <option value="">— Select Premise —</option>
                {premises.map(p => <option key={p}>{p}</option>)}
              </select>
              {premises.length === 0 && (
                <div style={{fontSize:10.5,color:'var(--amber)',marginTop:4}}>
                  No premises in master data for {form.comm}. Enter machine manually below.
                </div>
              )}
            </div>

            {/* Machine */}
            <div className="form-group">
              <label className="form-label">Machine *</label>
              {machines.length > 0
                ? <select className="form-select" value={form.machine} onChange={e => up('machine', e.target.value)}>
                    <option value="">— Select Machine —</option>
                    {machines.map(m => <option key={m}>{m}</option>)}
                  </select>
                : <input className="form-input" style={{fontFamily:'var(--mono)',fontSize:12}}
                    placeholder="M-XXX-000 (CHTPR...)" value={form.machine}
                    onChange={e => up('machine', e.target.value)} />
              }
            </div>

            <div className="form-group">
              <label className="form-label">Correspondence Ref. No.</label>
              <input className="form-input" style={{fontFamily:'var(--mono)',fontSize:12}}
                placeholder="RO/DEL-E/2026/000" value={form.reqRef}
                onChange={e => up('reqRef', e.target.value)} />
            </div>

            <div className="form-group">
              <label className="form-label">Notes / Reason</label>
              <textarea className="form-textarea" value={form.notes}
                onChange={e => up('notes', e.target.value)}
                placeholder="State reason for sealing/unsealing event..." />
            </div>
          </div>

          {/* Right: Jurisdiction */}
          <div>
            <div className="card" style={{marginBottom:12}}>
              <div className="card-title">GST Jurisdiction</div>

              <div className="form-group">
                <label className="form-label">GST Zone</label>
                {availZones.length === 1
                  ? <div className="field-locked">{form.zone} <small>· Locked to your jurisdiction</small></div>
                  : <select className="form-select" value={form.zone} onChange={e => {
                      up('zone', e.target.value);
                      up('comm', (COMMS[e.target.value]||[])[0] || '');
                      up('firm',''); up('machine','');
                    }}>
                      {availZones.map(z => <option key={z}>{z}</option>)}
                    </select>
                }
              </div>

              <div className="form-group">
                <label className="form-label">Commissionerate</label>
                {availComms.length === 1
                  ? <div className="field-locked">{form.comm} <small>· Locked</small></div>
                  : <select className="form-select" value={form.comm} onChange={e => {
                      up('comm', e.target.value); up('firm',''); up('machine','');
                    }}>
                      {availComms.map(c => <option key={c}>{c}</option>)}
                    </select>
                }
              </div>

              <div className="form-group">
                <label className="form-label">Division *</label>
                <select className="form-select" value={form.div} onChange={e => up('div', e.target.value)}>
                  {DIVISIONS.map(d => <option key={d}>{d}</option>)}
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Range</label>
                {availRanges.length === 1
                  ? <div className="field-locked">{form.range} <small>· Locked</small></div>
                  : <select className="form-select" value={form.range} onChange={e => up('range', e.target.value)}>
                      {availRanges.map(r => <option key={r}>{r}</option>)}
                    </select>
                }
              </div>

              <div className="form-group">
                <label className="form-label">Range Officer</label>
                {isNodal
                  ? <div className="field-locked">{user.name} <small>· You</small></div>
                  : <select className="form-select" value={form.rangeOfficer}
                      onChange={e => up('rangeOfficer', e.target.value)}>
                      <option value="">— Select Officer —</option>
                      {officers.map(o => <option key={o}>{o}</option>)}
                    </select>
                }
              </div>
            </div>

            <div className="warn-banner">
              <strong>SLA:</strong> Must be completed within <strong>3 working days</strong>.
              Penalty 10%/day from Day 4. After Day 7: 100% monthly lock rental.
            </div>

            <div style={{ display:'flex', gap:8 }}>
              <button type="button" className="btn-outline" style={{flex:1}} onClick={onCancel}>
                Cancel
              </button>
              <button type="submit" className="btn-primary" style={{flex:2}} disabled={!canSubmit}>
                Submit {form.type} Ticket →
              </button>
            </div>
          </div>
        </div>
      </form>
    </div>
  );
}

// ── TICKET DETAIL ───────────────────────────────────────────────────────────
function TicketDetail({ ticket, user, onBack, onUpdate }) {
  const [assignEng, setAssignEng] = useState(ticket.engineerId || '');
  const [rejectReason, setRejectReason] = useState('');
  const [showReject, setShowReject] = useState(false);

  const canApprove = ['super_admin','cbic_admin','bsnl_admin'].includes(user.role);
  const canAssign  = ['super_admin','cbic_admin','bsnl_admin','bsnl_supervisor'].includes(user.role);

  const scopedEngineers = ENGINEERS.filter(e =>
    user.zone === 'All Zones' || e.zone === ticket.zone
  );

  const now = () => new Date().toLocaleString('en-IN',{day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit',hour12:false});

  function approve() {
    onUpdate({ status:'Approved', approvedBy: user.name, approvedAt: now() });
  }
  function reject() {
    onUpdate({ status:'Rejected', notes:(ticket.notes||'') + ` | Rejected by ${user.name}: ${rejectReason}` });
    setShowReject(false);
  }
  function assign() {
    const eng = scopedEngineers.find(e => e.id === assignEng);
    onUpdate({ status:'Assigned', engineerId: assignEng, engineerName: eng?.name || '', assignedAt: now() });
  }

  return (
    <div>
      <div className="page-header">
        <div className="breadcrumb">
          <span style={{cursor:'pointer',color:'var(--navy)'}} onClick={onBack}>Tickets</span>
          <span>/</span> {ticket.id}
        </div>
        <div style={{display:'flex',alignItems:'center',justifyContent:'space-between'}}>
          <div>
            <div className="page-title">{ticket.id} — {ticket.type === 'ESE' ? 'Electronic Sealing' : 'Electronic Unsealing'}</div>
            <div className="page-subtitle">{ticket.firm} · {ticket.range}, {ticket.commissionerate}, {ticket.zone}</div>
          </div>
          <span className="pill" style={{
            background: (STATUS_COLOR[ticket.status]||'var(--navy)') + '22',
            color: STATUS_COLOR[ticket.status]||'var(--navy)',
            fontSize:13, padding:'5px 14px',
          }}>{ticket.status}</span>
        </div>
      </div>

      {/* Approve/Reject */}
      {canApprove && ['New','Pending'].includes(ticket.status) && (
        <div className="card" style={{marginBottom:12,borderLeft:'4px solid var(--amber)'}}>
          <div className="card-title">Action Required</div>
          {showReject
            ? <div>
                <div className="form-group">
                  <label className="form-label">Rejection Reason *</label>
                  <textarea className="form-textarea" value={rejectReason}
                    onChange={e => setRejectReason(e.target.value)} placeholder="State reason..." />
                </div>
                <div style={{display:'flex',gap:8}}>
                  <button className="btn-outline" onClick={() => setShowReject(false)}>Cancel</button>
                  <button style={{padding:'7px 16px',borderRadius:'var(--r)',border:'none',background:'var(--red)',color:'#fff',cursor:'pointer',fontFamily:'var(--font)',fontWeight:600,fontSize:12}}
                    onClick={reject} disabled={!rejectReason}>Confirm Reject</button>
                </div>
              </div>
            : <div style={{display:'flex',gap:8}}>
                <button style={{padding:'8px 18px',borderRadius:'var(--r)',border:'none',background:'var(--green)',color:'#fff',cursor:'pointer',fontFamily:'var(--font)',fontWeight:600,fontSize:12}} onClick={approve}>✓ Approve</button>
                <button style={{padding:'8px 18px',borderRadius:'var(--r)',border:'none',background:'var(--red)',color:'#fff',cursor:'pointer',fontFamily:'var(--font)',fontWeight:600,fontSize:12}} onClick={() => setShowReject(true)}>✗ Reject</button>
              </div>
          }
        </div>
      )}

      {/* Assign engineer */}
      {canAssign && ticket.status === 'Approved' && (
        <div className="card" style={{marginBottom:12,borderLeft:'4px solid var(--blue)'}}>
          <div className="card-title">Assign Field Engineer</div>
          <div style={{display:'flex',gap:8,alignItems:'center'}}>
            <select className="form-select" style={{flex:1}} value={assignEng} onChange={e => setAssignEng(e.target.value)}>
              <option value="">— Select Engineer —</option>
              {scopedEngineers.map(e => <option key={e.id} value={e.id}>{e.name} ({e.zone})</option>)}
            </select>
            <button className="btn-primary" onClick={assign} disabled={!assignEng}>Assign →</button>
          </div>
        </div>
      )}

      <div className="grid-2">
        <div className="card">
          <div className="card-title">Ticket Information</div>
          {[
            ['Ticket ID',    ticket.id,          true],
            ['Event Type',   ticket.type,         false],
            ['Priority',     ticket.priority,     false],
            ['Request Ref',  ticket.reqRef||'—',  true],
            ['Date',         ticket.reqDate,       true],
            ['SLA Deadline', ticket.slaDeadline,  true],
            ['Approved By',  ticket.approvedBy||'—', false],
            ['Approved At',  ticket.approvedAt||'—', true],
            ['Engineer',     ticket.engineerName||'—', false],
          ].map(([label,value,mono]) => (
            <div key={label} style={{display:'flex',justifyContent:'space-between',padding:'6px 0',borderBottom:'1px solid var(--border)'}}>
              <span style={{fontSize:11.5,color:'var(--text3)',fontWeight:600}}>{label}</span>
              <span style={{fontSize:11.5,fontFamily:mono?'var(--mono)':'var(--font)',color:'var(--text)',fontWeight:500}}>{value}</span>
            </div>
          ))}
          {ticket.notes && (
            <div style={{marginTop:8,padding:'8px 10px',background:'var(--navy-xlight)',borderRadius:4,fontSize:11,color:'var(--navy)',lineHeight:1.6,borderLeft:'3px solid var(--navy3)'}}>
              {ticket.notes}
            </div>
          )}
        </div>

        <div className="card">
          <div className="card-title">GST Jurisdiction</div>
          {[
            ['HSNS Reg.',       ticket.hsnsReg||'—',        true],
            ['Machine No.',     ticket.machine,              true],
            ['Machine Reg.',    ticket.machineReg||'—',     true],
            ['Firm',            ticket.firm,                 false],
            ['GSTIN',           ticket.gstin||'—',          true],
            ['Zone',            ticket.zone,                 false],
            ['Commissionerate', ticket.commissionerate,      false],
            ['Division',        ticket.division,             false],
            ['Range',           ticket.range,                false],
            ['Range Officer',   ticket.rangeOfficer,         false],
          ].map(([label,value,mono]) => (
            <div key={label} style={{display:'flex',justifyContent:'space-between',padding:'5px 0',borderBottom:'1px solid var(--border)'}}>
              <span style={{fontSize:11,color:'var(--text3)',fontWeight:600}}>{label}</span>
              <span style={{fontSize:11,fontFamily:mono?'var(--mono)':'var(--font)',color:'var(--text)',maxWidth:'55%',textAlign:'right'}}>{value||'—'}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ── TICKET LIST ─────────────────────────────────────────────────────────────
function TicketList({ user, tickets, onNew, onView }) {
  const [filterStatus, setFilterStatus] = useState('all');
  const [filterType,   setFilterType]   = useState('all');

  const visible = useMemo(() => {
    let arr = Array.isArray(tickets) ? tickets : [];
    // Scope by jurisdiction
    if (user.zone !== 'All Zones' &&
        !['super_admin','cbic_admin','bsnl_admin','auditor'].includes(user.role)) {
      arr = arr.filter(t => t.zone === user.zone);
      if (user.comm) arr = arr.filter(t => t.commissionerate === user.comm);
    }
    if (user.role === 'field_engineer') {
      arr = arr.filter(t => t.engineerId === user.engineerId);
    }
    if (filterStatus !== 'all') arr = arr.filter(t => t.status === filterStatus);
    if (filterType   !== 'all') arr = arr.filter(t => t.type   === filterType);
    return arr;
  }, [tickets, user, filterStatus, filterType]);

  const canCreate = user.role === 'nodal_officer';
  const isAuditor = user.role === 'auditor';

  return (
    <div>
      <div className="page-header">
        <div className="breadcrumb"><span>Home</span><span>/</span>DGGI Seal Tickets</div>
        <div style={{display:'flex',alignItems:'flex-end',justifyContent:'space-between'}}>
          <div>
            <div className="page-title">DGGI Sealing / Unsealing Ticket Register</div>
            <div className="page-subtitle">
              {user.comm ? `${user.comm} · ${user.zone}` :
               user.zone === 'All Zones' ? 'PAN India — All Zones' : user.zone}
              {isAuditor && ' · Read-only view'}
            </div>
          </div>
          {canCreate && <button className="btn-primary" onClick={onNew}>+ New Ticket</button>}
        </div>
      </div>

      {isAuditor && <div className="info-banner">Read-only access. You can view tickets but cannot create, approve or modify records.</div>}

      {/* KPI mini-bar */}
      <div className="kpi-grid" style={{gridTemplateColumns:'repeat(5,1fr)',marginBottom:12}}>
        {[
          {label:'Total',       value:visible.length,                                              accent:'var(--navy)'},
          {label:'New',         value:visible.filter(t=>t.status==='New').length,                  accent:'var(--blue)'},
          {label:'In Progress', value:visible.filter(t=>['Approved','Assigned','In Progress'].includes(t.status)).length, accent:'var(--amber)'},
          {label:'Completed',   value:visible.filter(t=>t.status==='Completed').length,            accent:'var(--green)'},
          {label:'SLA Breach',  value:visible.filter(t=>t.status==='Breach').length,               accent:'var(--red)'},
        ].map(k => (
          <div key={k.label} className="kpi" style={{'--kpi-accent':k.accent}}>
            <div className="kpi-label">{k.label}</div>
            <div className="kpi-value" style={{fontSize:22}}>{k.value}</div>
          </div>
        ))}
      </div>

      <div className="card">
        <div className="filter-bar">
          {['all','New','Pending','Approved','Assigned','In Progress','Completed','Breach','Rejected'].map(s => (
            <button key={s} className={`filter-btn ${filterStatus===s?'active':''}`}
              onClick={() => setFilterStatus(s)}>{s === 'all' ? 'All Status' : s}</button>
          ))}
          <button className={`filter-btn ${filterType==='ESE'?'active':''}`}
            onClick={() => setFilterType(f => f==='ESE'?'all':'ESE')}>🔒 ESE</button>
          <button className={`filter-btn ${filterType==='EUE'?'active':''}`}
            onClick={() => setFilterType(f => f==='EUE'?'all':'EUE')}>🔓 EUE</button>
        </div>

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Ticket ID</th><th>Type</th><th>Firm</th><th>Machine</th>
                <th>Jurisdiction</th><th>Officer</th><th>Date</th>
                <th>Priority</th><th>Status</th><th></th>
              </tr>
            </thead>
            <tbody>
              {visible.map(t => (
                <tr key={t.id} className="clickable" onClick={() => onView(t)}>
                  <td><span className="chip">{t.id}</span></td>
                  <td><span style={{fontSize:10,padding:'1px 6px',borderRadius:3,fontWeight:700,
                    background:t.type==='ESE'?'var(--navy-light)':'var(--amber-light)',
                    color:t.type==='ESE'?'var(--navy)':'var(--saffron)'}}>{t.type}</span></td>
                  <td style={{fontSize:11.5,maxWidth:150,overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap'}}>{t.firm}</td>
                  <td style={{fontFamily:'var(--mono)',fontSize:11,color:'var(--text3)'}}>{t.machine}</td>
                  <td style={{fontSize:11.5}}>{t.range}, {t.commissionerate}</td>
                  <td style={{fontSize:11.5}}>{t.rangeOfficer}</td>
                  <td style={{fontFamily:'var(--mono)',fontSize:11,color:'var(--text3)'}}>{t.reqDate}</td>
                  <td style={{fontSize:11,fontWeight:700,color:PRIORITY_COLOR[t.priority]}}>{t.priority}</td>
                  <td><span className="pill" style={{
                    background:(STATUS_COLOR[t.status]||'var(--navy)')+'22',
                    color:STATUS_COLOR[t.status]||'var(--navy)',
                  }}>{t.status}</span></td>
                  <td onClick={e=>e.stopPropagation()}>
                    <button className="btn-outline btn-sm" onClick={() => onView(t)}>View</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div style={{marginTop:8,fontSize:11,color:'var(--text3)'}}>
          Showing {visible.length} ticket{visible.length!==1?'s':''} · Click any row for details
        </div>
      </div>
    </div>
  );
}

// ── MAIN EXPORT ─────────────────────────────────────────────────────────────
export default function DGGITickets({ user, tickets, setTickets }) {
  const [view,     setView]     = useState('list');  // 'list' | 'create' | 'detail'
  const [selected, setSelected] = useState(null);
  const [success,  setSuccess]  = useState('');

  function handleCreate(form) {
    const now    = new Date();
    const sla    = new Date(now.getTime() + 3*24*60*60*1000);
    const fmtDate = d => d.toLocaleDateString('en-IN',{day:'2-digit',month:'short',year:'numeric'});

    const ticket = {
      id:             makeId(tickets),
      type:           form.type,
      status:         'New',
      priority:       form.priority,
      machine:        form.machine.split(' ')[0] || form.machine,
      machineReg:     (form.machine.match(/\(([^)]+)\)/) || ['',''])[1],
      firm:           'M/s ' + form.firm,
      gstin:          form.gstin,
      zone:           form.zone,
      commissionerate:form.comm,
      division:       form.div,
      range:          form.range,
      rangeOfficer:   form.rangeOfficer,
      reqDate:        fmtDate(now),
      reqRef:         form.reqRef || `RO/AUTO/2026/${Math.floor(Math.random()*999)}`,
      hsnsReg:        form.hsnsReg,
      notes:          form.notes,
      engineerId:     '', engineerName:'',
      approvedBy:'',  approvedAt:'', assignedAt:'',
      slaDeadline:    fmtDate(sla) + ' 23:59',
    };

    setTickets(prev => [ticket, ...prev]);
    setSuccess(ticket.id);
    setView('list');
    setTimeout(() => setSuccess(''), 6000);
  }

  function handleUpdate(changes) {
    setTickets(prev => prev.map(t => t.id === selected.id ? {...t, ...changes} : t));
    setSelected(prev => ({...prev, ...changes}));
  }

  if (view === 'create') {
    return <CreateForm user={user} onSubmit={handleCreate} onCancel={() => setView('list')} />;
  }

  if (view === 'detail' && selected) {
    const live = tickets.find(t => t.id === selected.id) || selected;
    return (
      <TicketDetail
        ticket={live} user={user}
        onBack={() => setView('list')}
        onUpdate={handleUpdate}
      />
    );
  }

  return (
    <>
      {success && (
        <div className="success-banner">
          <span style={{fontSize:18,color:'var(--green)'}}>✓</span>
          <div>
            <div style={{fontWeight:700,color:'var(--green)',fontSize:13}}>Ticket {success} created</div>
            <div style={{fontSize:11.5,color:'var(--text2)',fontFamily:'var(--mono)'}}>
              Sent to BSNL Admin for approval · 72-hr SLA started
            </div>
          </div>
        </div>
      )}
      <TicketList
        user={user} tickets={tickets}
        onNew={() => setView('create')}
        onView={t => { setSelected(t); setView('detail'); }}
      />
    </>
  );
}
