// ─── GST MASTER DATA ───────────────────────────────────────────────────────
// Single source of truth for all static GST hierarchy, premises, machines

export const ZONES = [
  'Delhi Zone','Mumbai Zone','Chennai Zone','Kolkata Zone',
  'Bengaluru Zone','Hyderabad Zone','Ahmedabad Zone',
];

export const COMMS = {
  'Delhi Zone':    ['Delhi South','Delhi North','Delhi East','Delhi West','Gurugram','Noida','Faridabad'],
  'Mumbai Zone':   ['Mumbai Central','Mumbai South','Mumbai West','Thane','Pune I','Pune II','Nashik'],
  'Chennai Zone':  ['Chennai North','Chennai South','Chennai Outer','Coimbatore','Madurai'],
  'Kolkata Zone':  ['Kolkata South','Kolkata North','Howrah','Haldia','Bhubaneswar'],
  'Bengaluru Zone':['Bengaluru NW','Bengaluru South','Mysuru','Belagavi'],
  'Hyderabad Zone':['Hyderabad I','Hyderabad II','Guntur','Visakhapatnam'],
  'Ahmedabad Zone':['Ahmedabad South','Ahmedabad North','Surat','Rajkot','Vadodara I'],
};

export const DIVISIONS = ['Division I','Division II','Division III','Division IV','Division V'];
export const RANGES    = ['Range I','Range II','Range III','Range IV','Range V','Range VI'];

export const PREMISES = {
  'Delhi East':  ['Shri Ganesh Tobacco Pvt Ltd','Eastern Leaf Corp','DeltaSmoke Industries'],
  'Delhi North': ['North India Pan Works','Capital Tobacco Co'],
  'Delhi South': ['South Delhi Tobacco Ltd'],
  'Delhi West':  ['West Delhi Pan Corp'],
  'Gurugram':    ['Haryana Spice Foods Ltd','GGN Masala Corp'],
  'Noida':       ['Noida Leaf Industries'],
  'Faridabad':   ['Faridabad Pan Works'],
  'Mumbai West': ['Bombay Pan Masala Works','West Coast Tobacco'],
  'Mumbai Central':['Marine Lines Tobacco','Central Pan Co'],
  'Mumbai South':['South Bombay Leaf Co'],
  'Thane':       ['Thane Pan Industries'],
  'Pune I':      ['Pune Tobacco Works'],
  'Pune II':     ['Deccan Pan Co'],
  'Nashik':      ['Nashik Leaf Corp'],
  'Hyderabad I': ['Deccan Tobacco Products','Hyderabad Pan Works'],
  'Hyderabad II':['Secunderabad Tobacco Co'],
  'Chennai North':['South India Tobacco Ltd','Madras Pan Corp'],
  'Chennai South':['Chennai South Leaf Co'],
  'Kolkata South':['Eastern Masala Pvt Ltd','Bengal Tobacco Co'],
  'Kolkata North':['North Bengal Leaf Co'],
};

export const MACHINES = {
  'Shri Ganesh Tobacco Pvt Ltd': ['M-DEL-014 (CHTPR0365MHS00320001)','M-DEL-015 (CHTPR0365MHS00320002)'],
  'Eastern Leaf Corp':           ['M-DEL-016 (CHTPR0365MHS00320003)'],
  'DeltaSmoke Industries':       ['M-DEL-017 (CHTPR0365MHS00320004)'],
  'Bombay Pan Masala Works':     ['M-MUM-047 (CHTPR0365MHS00300001)','M-MUM-048 (CHTPR0365MHS00300002)'],
  'Deccan Tobacco Products':     ['M-HYD-033 (CHTPR0365MHS00330001)'],
  'South India Tobacco Ltd':     ['M-CHN-018 (CHTPR0365MHS00180001)'],
  'Eastern Masala Pvt Ltd':      ['M-PAT-005 (CHTPR0365MHS00190001)'],
  'Haryana Spice Foods Ltd':     ['M-GGN-022 (CHTPR0365MHS00220001)'],
  'North India Pan Works':       ['M-DEL-020 (CHTPR0365MHS00210001)'],
  'Capital Tobacco Co':          ['M-DEL-021 (CHTPR0365MHS00210002)'],
};

export const OFFICERS = {
  'Delhi East':   ['Rajesh Kumar Sharma','Anil Verma','Sunita Rao'],
  'Delhi North':  ['Vikram Nair','Prerna Gupta'],
  'Delhi South':  ['Rajan Mehta','Anita Sharma'],
  'Delhi West':   ['Suresh Kumar','Nidhi Joshi'],
  'Gurugram':     ['Neha Verma','Pankaj Kumar'],
  'Noida':        ['Amit Tiwari','Ritu Singh'],
  'Faridabad':    ['Deepak Yadav'],
  'Mumbai West':  ['Priya Sharma','Ashok Mehta'],
  'Mumbai Central':['Rohit Kapoor','Smita Patil'],
  'Hyderabad I':  ['Kavitha Reddy','Suresh Rao'],
  'Chennai North':['Suresh Patel','Meera Iyer'],
  'Kolkata South':['Vikram Yadav','Ratan Das'],
};

export const ENGINEERS = [
  { id:'eng-001', name:'Rajendra Prasad',  zone:'Delhi Zone' },
  { id:'eng-002', name:'Suresh Patil',     zone:'Mumbai Zone' },
  { id:'eng-003', name:'Dinesh Kumar',     zone:'Delhi Zone' },
  { id:'eng-004', name:'Ramesh Babu',      zone:'Hyderabad Zone' },
  { id:'eng-005', name:'Anil Shah',        zone:'Ahmedabad Zone' },
];

// ─── USERS (9 demo users) ───────────────────────────────────────────────────
export const USERS = [
  // CBIC / GST Officers
  {
    email:'admin@elsm.in', password:'Admin@1234',
    role:'super_admin', name:'Arvind Kumar Singh',
    zone:'All Zones', comm:null, range:null,
    tab:'cbic',
  },
  {
    email:'cbic.admin@gstin.gov.in', password:'Admin@1234',
    role:'cbic_admin', name:'Deepak Mehrotra',
    zone:'Delhi Zone', comm:'Delhi East', range:null,
    tab:'cbic',
  },
  {
    email:'raj.kumar@gstin.gov.in', password:'Admin@1234',
    role:'nodal_officer', name:'Rajesh Kumar Sharma',
    zone:'Delhi Zone', comm:'Delhi East', range:'Range I',
    tab:'cbic',
  },
  {
    email:'priya.sharma@gstin.gov.in', password:'Admin@1234',
    role:'nodal_officer', name:'Priya Sharma',
    zone:'Mumbai Zone', comm:'Mumbai West', range:'Range IV',
    tab:'cbic',
  },
  {
    email:'kavitha.reddy@gstin.gov.in', password:'Admin@1234',
    role:'nodal_officer', name:'Kavitha Reddy',
    zone:'Hyderabad Zone', comm:'Hyderabad I', range:'Range V',
    tab:'cbic',
  },
  {
    email:'auditor@cbic.gov.in', password:'Admin@1234',
    role:'auditor', name:'Sunita Verma',
    zone:'All Zones', comm:null, range:null,
    tab:'cbic',
  },
  // BSNL Personnel
  {
    email:'bsnl.admin@bsnl.co.in', password:'Admin@1234',
    role:'bsnl_admin', name:'Ankit Sharma',
    zone:'All Zones', comm:null, range:null,
    tab:'bsnl',
  },
  {
    email:'supervisor@bsnl.co.in', password:'Admin@1234',
    role:'bsnl_supervisor', name:'Ramesh Chandra Gupta',
    zone:'Delhi Zone', comm:null, range:null,
    tab:'bsnl',
  },
  {
    email:'engineer@bsnl.co.in', password:'Admin@1234',
    role:'field_engineer', name:'Rajendra Prasad',
    zone:'Delhi Zone', comm:null, range:null,
    engineerId:'eng-001',
    tab:'bsnl',
  },
];

// ─── INITIAL TICKETS (seed data) ───────────────────────────────────────────
export const INITIAL_TICKETS = [
  {
    id:'TKT-2026-0041', type:'ESE', status:'Assigned', priority:'High',
    machine:'M-DEL-014', machineReg:'CHTPR0365MHS00320001',
    firm:'M/s Shri Ganesh Tobacco Pvt Ltd', gstin:'07AABCS1429B1Z5',
    zone:'Delhi Zone', commissionerate:'Delhi East', division:'Division I', range:'Range I',
    rangeOfficer:'Rajesh Kumar Sharma',
    reqDate:'10 Mar 2026', reqRef:'RO/DEL-E/2026/041',
    engineerId:'eng-001', engineerName:'Rajendra Prasad',
    approvedBy:'Ankit Sharma', approvedAt:'11 Mar 2026 10:30',
    assignedAt:'11 Mar 2026 14:00',
    slaDeadline:'13 Mar 2026 23:59', notes:'Routine sealing',
  },
  {
    id:'TKT-2026-0042', type:'ESE', status:'In Progress', priority:'Urgent',
    machine:'M-MUM-047', machineReg:'CHTPR0365MHS00300001',
    firm:'M/s Bombay Pan Masala Works', gstin:'27AABCB1234B1Z1',
    zone:'Mumbai Zone', commissionerate:'Mumbai West', division:'Division II', range:'Range IV',
    rangeOfficer:'Priya Sharma',
    reqDate:'12 Mar 2026', reqRef:'RO/MUM-W/2026/042',
    engineerId:'eng-002', engineerName:'Suresh Patil',
    approvedBy:'Ankit Sharma', approvedAt:'12 Mar 2026 09:00',
    assignedAt:'12 Mar 2026 11:00',
    slaDeadline:'15 Mar 2026 23:59', notes:'',
  },
  {
    id:'TKT-2026-0043', type:'EUE', status:'Pending', priority:'Normal',
    machine:'M-MUM-048', machineReg:'CHTPR0365MHS00300002',
    firm:'M/s Bombay Pan Masala Works', gstin:'27AABCB1234B1Z1',
    zone:'Mumbai Zone', commissionerate:'Mumbai West', division:'Division II', range:'Range IV',
    rangeOfficer:'Priya Sharma',
    reqDate:'14 Mar 2026', reqRef:'RO/MUM-W/2026/043',
    engineerId:'', engineerName:'',
    approvedBy:'', approvedAt:'', assignedAt:'',
    slaDeadline:'17 Mar 2026 23:59', notes:'Machine maintenance due',
  },
  {
    id:'TKT-2026-0044', type:'ESE', status:'Completed', priority:'Normal',
    machine:'M-GGN-022', machineReg:'CHTPR0365MHS00220001',
    firm:'M/s Haryana Spice Foods Ltd', gstin:'06AABCH5678C1Z3',
    zone:'Delhi Zone', commissionerate:'Gurugram', division:'Division III', range:'Range II',
    rangeOfficer:'Neha Verma',
    reqDate:'05 Mar 2026', reqRef:'RO/GGN/2026/044',
    engineerId:'eng-003', engineerName:'Dinesh Kumar',
    approvedBy:'Ankit Sharma', approvedAt:'06 Mar 2026 10:00',
    assignedAt:'06 Mar 2026 12:00',
    slaDeadline:'08 Mar 2026 23:59', notes:'',
  },
  {
    id:'TKT-2026-0045', type:'EUE', status:'Assigned', priority:'High',
    machine:'M-HYD-033', machineReg:'CHTPR0365MHS00330001',
    firm:'M/s Deccan Tobacco Products', gstin:'36AABCD9012D1Z7',
    zone:'Hyderabad Zone', commissionerate:'Hyderabad I', division:'Division I', range:'Range V',
    rangeOfficer:'Kavitha Reddy',
    reqDate:'15 Mar 2026', reqRef:'RO/HYD-I/2026/045',
    engineerId:'eng-004', engineerName:'Ramesh Babu',
    approvedBy:'Ankit Sharma', approvedAt:'16 Mar 2026 09:30',
    assignedAt:'16 Mar 2026 11:30',
    slaDeadline:'18 Mar 2026 23:59', notes:'',
  },
  {
    id:'TKT-2026-0046', type:'ESE', status:'Breach', priority:'Critical',
    machine:'M-PAT-005', machineReg:'CHTPR0365MHS00190001',
    firm:'M/s Eastern Masala Pvt Ltd', gstin:'20AABCE3456E1Z2',
    zone:'Kolkata Zone', commissionerate:'Kolkata South', division:'Division I', range:'Range I',
    rangeOfficer:'Vikram Yadav',
    reqDate:'01 Mar 2026', reqRef:'RO/KOL-S/2026/046',
    engineerId:'', engineerName:'',
    approvedBy:'', approvedAt:'', assignedAt:'',
    slaDeadline:'04 Mar 2026 23:59', notes:'SLA breached — no engineer assigned',
  },
  {
    id:'TKT-2026-0047', type:'ESE', status:'New', priority:'Normal',
    machine:'M-CHN-018', machineReg:'CHTPR0365MHS00180001',
    firm:'M/s South India Tobacco Ltd', gstin:'33AABCS7890S1Z5',
    zone:'Chennai Zone', commissionerate:'Chennai North', division:'Division II', range:'Range III',
    rangeOfficer:'Suresh Patel',
    reqDate:'20 Mar 2026', reqRef:'RO/CHN-N/2026/047',
    engineerId:'', engineerName:'',
    approvedBy:'', approvedAt:'', assignedAt:'',
    slaDeadline:'23 Mar 2026 23:59', notes:'',
  },
];
