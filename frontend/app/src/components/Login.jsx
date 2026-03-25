import { useState } from 'react';
import { USERS } from '../data/gstMaster';

const ROLE_LABELS = {
  super_admin:    'Super Admin',
  cbic_admin:     'CBIC Admin',
  nodal_officer:  'Range Officer',
  auditor:        'Auditor',
  bsnl_admin:     'BSNL Admin',
  bsnl_supervisor:'BSNL Supervisor',
  field_engineer: 'Field Engineer',
};

export default function Login({ onLogin }) {
  const [tab, setTab]         = useState('cbic');
  const [email, setEmail]     = useState('');
  const [password, setPassword] = useState('');
  const [step, setStep]       = useState('creds'); // 'creds' | 'otp'
  const [otp, setOtp]         = useState('');
  const [pending, setPending] = useState(null);
  const [error, setError]     = useState('');

  const cbicUsers = USERS.filter(u => u.tab === 'cbic');
  const bsnlUsers = USERS.filter(u => u.tab === 'bsnl');

  function quickFill(user) {
    setEmail(user.email);
    setPassword(user.password);
    setTab(user.tab);
    setError('');
  }

  function handleSubmit(e) {
    e.preventDefault();
    setError('');
    const user = USERS.find(u => u.email === email && u.password === password);
    if (!user) { setError('Invalid email or password.'); return; }
    // Simulate OTP step
    setPending(user);
    setStep('otp');
    setOtp('');
  }

  function handleOtp(e) {
    e.preventDefault();
    // Demo: any 6-digit OTP works
    if (otp.length !== 6 || !/^\d+$/.test(otp)) {
      setError('Enter the 6-digit OTP sent to your registered mobile.');
      return;
    }
    // Strip password before storing
    const { password: _pw, ...safeUser } = pending;
    localStorage.setItem('elsm_user', JSON.stringify(safeUser));
    onLogin(safeUser);
  }

  function back() { setStep('creds'); setError(''); setPending(null); }

  const tabUsers = tab === 'cbic' ? cbicUsers : bsnlUsers;

  return (
    <div className="login-page">
      <div className="login-box">

        {/* Logo */}
        <div className="login-logo">
          <div style={{ fontSize: 28, marginBottom: 4 }}>⚙️</div>
          <div className="login-logo-title">ELSM Portal</div>
          <div className="login-logo-sub">
            CBIC · Electronic Lock Solution for Machines
          </div>
          <div style={{ fontSize: 10, color: 'var(--text3)', marginTop: 2 }}>
            Government of India · Ministry of Finance · CBIC
          </div>
        </div>

        {step === 'creds' ? (
          <>
            {/* Tabs */}
            <div className="login-tabs">
              <div className={`login-tab ${tab === 'cbic' ? 'active' : ''}`} onClick={() => { setTab('cbic'); setError(''); }}>
                🏛️ CBIC / GST Officers
              </div>
              <div className={`login-tab ${tab === 'bsnl' ? 'active' : ''}`} onClick={() => { setTab('bsnl'); setError(''); }}>
                📡 BSNL Personnel
              </div>
            </div>

            {/* Quick login buttons */}
            <div style={{ fontSize: 10.5, color: 'var(--text3)', marginBottom: 8, fontWeight: 600 }}>
              QUICK LOGIN (DEMO)
            </div>
            <div className="quick-logins">
              {tabUsers.map(u => (
                <button key={u.email} className="quick-btn" onClick={() => quickFill(u)}>
                  <strong>{u.name.split(' ').slice(0,2).join(' ')}</strong>
                  <span>{ROLE_LABELS[u.role]}</span>
                </button>
              ))}
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label className="form-label">Email / User ID</label>
                <input className="form-input" type="email" value={email}
                  onChange={e => setEmail(e.target.value)} placeholder="you@gstin.gov.in" required />
              </div>
              <div className="form-group">
                <label className="form-label">Password</label>
                <input className="form-input" type="password" value={password}
                  onChange={e => setPassword(e.target.value)} placeholder="••••••••" required />
              </div>
              {error && <div style={{ color: 'var(--red)', fontSize: 12, marginBottom: 10 }}>{error}</div>}
              <button className="btn-primary" style={{ width: '100%', padding: '10px' }} type="submit">
                Sign In →
              </button>
            </form>

            <div style={{ textAlign: 'center', fontSize: 10.5, color: 'var(--text3)', marginTop: 16 }}>
              Demo password for all users: <strong>Admin@1234</strong>
            </div>
          </>
        ) : (
          /* OTP Step */
          <form onSubmit={handleOtp}>
            <div style={{ textAlign: 'center', marginBottom: 20 }}>
              <div style={{ fontSize: 32, marginBottom: 8 }}>📱</div>
              <div style={{ fontWeight: 700, color: 'var(--navy)', fontSize: 15 }}>OTP Verification</div>
              <div style={{ fontSize: 12, color: 'var(--text3)', marginTop: 4 }}>
                Enter the 6-digit OTP sent to your registered mobile number.
              </div>
              <div style={{ fontSize: 11.5, fontWeight: 600, color: 'var(--navy)', marginTop: 8 }}>
                {pending?.name} · {ROLE_LABELS[pending?.role]}
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">OTP</label>
              <input className="form-input" type="text" maxLength={6}
                value={otp} onChange={e => setOtp(e.target.value.replace(/\D/g,''))}
                placeholder="______" style={{ textAlign: 'center', fontSize: 22, letterSpacing: 8, fontFamily: 'var(--mono)' }}
                autoFocus required />
              <div style={{ fontSize: 10.5, color: 'var(--text3)', marginTop: 4 }}>
                Demo: enter any 6 digits e.g. 123456
              </div>
            </div>

            {error && <div style={{ color: 'var(--red)', fontSize: 12, marginBottom: 10 }}>{error}</div>}

            <div style={{ display: 'flex', gap: 8 }}>
              <button type="button" className="btn-outline" style={{ flex: 1 }} onClick={back}>← Back</button>
              <button type="submit" className="btn-primary" style={{ flex: 2 }}>Verify & Login</button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
