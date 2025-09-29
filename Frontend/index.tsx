import React, { useState, useEffect, useMemo, createContext, useContext } from 'react';
import { createRoot } from 'react-dom/client';
import { GoogleGenAI, GenerateContentResponse, Type } from "@google/genai";

// --- TYPES AND INTERFACES ---
type Role = 'Staff' | 'Manager' | 'Director' | 'Board Member' | 'Admin';
type Department = 'Operations' | 'HR' | 'Finance' | 'Legal' | 'IT' | 'Safety' | 'All' | 'Engineering' | 'Maintenance';
type Priority = 'High' | 'Medium' | 'Low';
type DocType = 'Schedule' | 'Policy' | 'Report' | 'Contract' | 'Notice' | 'Audit' | 'Claim' | 'Research';
type DocSource = 'Email' | 'SharePoint' | 'Scanned' | 'Maximo' | 'Web Dashboard';
type SensorStatus = 'normal' | 'warning' | 'critical';

interface User {
  username: string; // Should be an email
  role: Role;
  department: Department;
}

interface Document {
  id: number;
  sender: string;
  subject:string;
  body: string;
  date: string;
  departments: Department[];
  accessExpiresIn?: string;
  language: string;
  critical: boolean;
  priority: Priority;
  docType: DocType;
  source: DocSource;
  summary: {
      en: string;
      ml: string;
  };
  roleSpecificSummaries: {
    Staff: string;
    Manager: string;
    Director: string;
  },
  sharedWith?: string[]; // Array of usernames
  summaryError?: boolean;
  attachmentFilename?: string;
  dueDate?: string;
}

interface AuditLogEvent {
    id: number;
    timestamp: string;
    username: string;
    action: string;
    details: string;
}

interface Sensor {
  id: number;
  name: string;
  type: string;
  status: SensorStatus;
  currentValue: string;
  unit: string;
  threshold: string;
  location: string;
  lastUpdate: string;
  icon: string;
}


// --- MOCK DATA & CONFIG ---
const mockUsers: Record<string, { password?: string; role: Role; department: Department }> = {
  'admin@kmrl.co.in': { password: 'password123', role: 'Admin', department: 'All' },
  'board@kmrl.co.in': { password: 'password123', role: 'Board Member', department: 'All' },
  'director.ops@kmrl.co.in': { password: 'password123', role: 'Director', department: 'Operations' },
  'director.hr@kmrl.co.in': { password: 'password123', role: 'Director', department: 'HR' },
  'manager.fin@kmrl.co.in': { password: 'password123', role: 'Manager', department: 'Finance' },
  'staff.safety@kmrl.co.in': { password: 'password123', role: 'Staff', department: 'Safety' },
  'staff.legal@kmrl.co.in': { password: 'password123', role: 'Staff', department: 'Legal' },
};
// Add old usernames for compatibility with saved sessions
mockUsers['admin'] = mockUsers['admin@kmrl.co.in'];
mockUsers['board'] = mockUsers['board@kmrl.co.in'];

type EditableRole = 'Staff' | 'Manager' | 'Director';
const initialPermissions: Record<string, Record<EditableRole, boolean>> = {
    'View Own Dept Docs': { Staff: true, Manager: true, Director: true },
    'View All Dept Docs': { Staff: false, Manager: false, Director: true },
    'Approve Documents': { Staff: false, Manager: true, Director: true },
    'Forward Documents': { Staff: false, Manager: true, Director: true },
    'Generate Reports': { Staff: false, Manager: true, Director: true },
    'Manage Users': { Staff: false, Manager: false, Director: false },
};

const mockDocuments: Document[] = [
    { 
        id: 9, 
        sender: 'it.support@kmrl.co.in', 
        subject: 'Planned Network Maintenance - Sat 27th July', 
        body: 'This is to inform all staff about a planned network maintenance window scheduled for this Saturday, July 27th, from 10 PM to 2 AM. During this period, access to internal network drives and SharePoint may be intermittent. Please save all your work before the maintenance window.', 
        date: '2024-07-22', 
        departments: ['IT'], 
        language: 'English', 
        critical: false, 
        priority: 'Medium',
        docType: 'Notice', 
        source: 'Email', 
        attachmentFilename: 'IT_Maintenance_Advisory.msg',
        summary: { en: '', ml: 'ഈ ശനിയാഴ്ച, ജൂലൈ 27-ന് രാത്രി 10 മുതൽ പുലർച്ചെ 2 വരെ നെറ്റ്‌വർക്ക് മെയിൻ്റനൻസ് കാരണം ഇൻ്റേണൽ നെറ്റ്‌വർക്ക് ഡ്രൈവുകളിലേക്കും ഷെയർപോയിൻ്റിലേക്കുമുള്ള സേവനം തടസ്സപ്പെടാം.' },
        roleSpecificSummaries: {
            Staff: 'Network access might be unavailable this Saturday from 10 PM to 2 AM due to maintenance. Save your work.',
            Manager: 'Inform your teams about the upcoming network maintenance on Saturday night (10 PM - 2 AM) to avoid work disruption.',
            Director: 'A scheduled IT network maintenance will occur this Saturday to improve system reliability, with minor, temporary disruptions to internal services.'
        },
        sharedWith: [],
        dueDate: '2024-07-27',
    },
    { 
        id: 10, 
        sender: 'travel.claims@externalcorp.com', 
        subject: 'Invoice and Claim Submission for Project Alpha Consultation', 
        body: 'Dear KMRL Finance, please find attached the final invoice for the consultation services provided for Project Alpha during Q2. The total claim amount is INR 75,000. Kindly process the payment at the earliest.', 
        date: '2024-07-22', 
        departments: ['Finance'], 
        language: 'English', 
        critical: false, 
        priority: 'Medium',
        docType: 'Claim', 
        source: 'Email', 
        attachmentFilename: 'Invoice_Alpha_Consult_Q2.pdf',
        summary: { en: '', ml: 'പ്രോജക്റ്റ് ആൽഫ കൺസൾട്ടേഷനുമായി ബന്ധപ്പെട്ട 75,000 രൂപയുടെ ഇൻവോയ്സ് പേയ്‌മെൻ്റിനായി സമർപ്പിച്ചിരിക്കുന്നു.' },
        roleSpecificSummaries: {
            Staff: 'A new payment claim of INR 75,000 has been received for Project Alpha consultation.',
            Manager: 'Review and approve the INR 75,000 invoice submitted for Q2 consultation services on Project Alpha.',
            Director: 'A payment claim for INR 75,000 has been logged for external consultation on Project Alpha, impacting the project budget.'
        },
        sharedWith: ['manager.fin@kmrl.co.in'],
        dueDate: '2024-08-10',
    },
    { 
        id: 1, sender: 'railcorp@example.com', subject: 'Urgent: Track Maintenance Schedule Q3', 
        body: 'Please review the attached track maintenance schedule for Q3. All departments must confirm their resource availability by EOD Friday. This is critical for ensuring uninterrupted service during the monsoon season.', 
        date: '2024-07-20', departments: ['Operations'], language: 'English', critical: true, priority: 'High',
        docType: 'Schedule', source: 'Email', attachmentFilename: 'Q3_Maintenance_Schedule.pdf',
        summary: { en: '', ml: 'ക്യു 3-ലെ ട്രാക്ക് അറ്റകുറ്റപ്പണി ഷെഡ്യൂൾ പ്രകാരം വെള്ളിയാഴ്ചയ്ക്കകം എല്ലാ വകുപ്പുകളും അവരുടെ ലഭ്യത ഉറപ്പാക്കണം.' },
        roleSpecificSummaries: {
            Staff: "Confirm your team's availability for the Q3 track maintenance by Friday.",
            Manager: "Review the Q3 maintenance schedule and confirm departmental resource availability by Friday to prevent service disruptions.",
            Director: "Critical Q3 track maintenance schedule requires immediate cross-departmental resource confirmation to ensure monsoon season service continuity."
        },
        sharedWith: ['manager.fin@kmrl.co.in'],
        dueDate: '2024-07-26',
    },
    { 
        id: 2, sender: 'hr@kmrl.co.in', subject: 'New Employee Onboarding Policy', 
        body: 'The updated employee onboarding policy is now effective. All managers are requested to familiarize themselves with the new procedures outlined in the document. A training session is scheduled for next week.', 
        date: '2024-07-19', departments: ['HR'], language: 'English', critical: false, priority: 'Medium',
        docType: 'Policy', source: 'SharePoint', attachmentFilename: 'Onboarding_Policy_v2.docx',
        summary: { en: '', ml: 'പുതിയ ജീവനക്കാർക്കുള്ള ഓൺബോർഡിംഗ് നയം നിലവിൽ വന്നു; മാനേജർമാർ പുതിയ നടപടിക്രമങ്ങൾ പഠിക്കണം.'},
        roleSpecificSummaries: {
            Staff: "Be aware of the new onboarding policy for new team members.",
            Manager: "Familiarize yourself with the new employee onboarding procedures and attend the upcoming training session.",
            Director: "A new employee onboarding policy has been implemented to standardize and improve the integration of new hires across the organization."
        },
        sharedWith: [],
        dueDate: '2024-07-31',
    },
    { 
        id: 3, sender: 'accounts@kmrl.co.in', subject: 'Q2 Financial Report Submission',
        body: 'This is a reminder that the Q2 financial reports are due by July 30th. Please ensure all expense claims are submitted through the portal before this date to be included in the quarterly assessment.', 
        date: '2024-07-18', departments: ['Finance'], language: 'English', critical: false, priority: 'High',
        docType: 'Report', source: 'Email', attachmentFilename: 'Q2_Finance_Guidelines.pdf',
        summary: { en: '', ml: 'ക്യു 2 സാമ്പത്തിക റിപ്പോർട്ടുകൾ ജൂലൈ 30-നകം സമർപ്പിക്കണം, എല്ലാ ചെലവുകളും അതിന് മുൻപ് പോർട്ടലിൽ നൽകണം.' },
        roleSpecificSummaries: {
            Staff: "Submit all your Q2 expense claims through the portal before July 30th.",
            Manager: "Ensure your team submits all Q2 expense claims via the portal before the July 30th deadline for the quarterly report.",
            Director: "The deadline for Q2 financial report submissions is July 30th, impacting the organization's quarterly financial assessment."
        },
        sharedWith: [],
    },
    { 
        id: 8, sender: 'gov.transport@nic.in', subject: 'അറിയിപ്പ്: സുരക്ഷാ ഓഡിറ്റ്', 
        body: 'കൊച്ചി മെട്രോയുടെ വാർഷിക സുരക്ഷാ ഓഡിറ്റ് അടുത്ത മാസം നടത്തുന്നതാണ്. ബന്ധപ്പെട്ട എല്ലാ വകുപ്പുകളും ആവശ്യമായ രേഖകൾ തയ്യാറാക്കി വെക്കേണ്ടതാണ്. കൂടുതൽ വിവരങ്ങൾ പിന്നീട് അറിയിക്കുന്നതാണ്.', 
        date: '2024-07-20', departments: ['Safety'], language: 'Malayalam', critical: true, priority: 'High',
        docType: 'Audit', source: 'Scanned', attachmentFilename: 'Audit_Notice_Malayalam.pdf',
        summary: { en: 'The annual safety audit for Kochi Metro will be conducted next month, and all concerned departments must prepare the necessary documents.', ml: '' },
        roleSpecificSummaries: {
            Staff: "Prepare all necessary documents for the upcoming annual safety audit.",
            Manager: "Ensure your department's records are updated and ready for the mandatory annual safety audit scheduled for next month.",
            Director: "A mandatory government safety audit is scheduled for next month, requiring all departments to be prepared and compliant."
        },
        sharedWith: ['staff.safety@kmrl.co.in'],
        dueDate: '2024-08-20',
    },
    { 
        id: 4, sender: 'legalteam@kmrl.co.in', subject: 'Contract Renewal: ABC Vending Services', 
        body: 'The contract with ABC Vending Services is up for renewal. The legal department has reviewed the terms and suggests modifications. Please provide feedback before the meeting on Monday.', 
        date: '2024-07-21', departments: ['Legal'], language: 'English', critical: false, priority: 'Medium',
        docType: 'Contract', source: 'Email', attachmentFilename: 'ABC_Vending_Contract.docx',
        summary: {en: '', ml: 'എബിസി വെൻഡിംഗ് സേവനങ്ങളുമായുള്ള കരാർ പുതുക്കുന്നതിന് നിയമവകുപ്പ് നിർദ്ദേശിച്ച മാറ്റങ്ങളിൽ തിങ്കളാഴ്ചത്തെ മീറ്റിംഗിന് മുൻപ് അഭിപ്രായം അറിയിക്കുക.'},
        roleSpecificSummaries: {
            Staff: "N/A for most staff.",
            Manager: "Provide feedback on the proposed modifications for the ABC Vending Services contract renewal before Monday's meeting.",
            Director: "The ABC Vending Services contract is under review for renewal with suggested legal modifications requiring senior feedback."
        },
        sharedWith: [],
    },
];

const mockAuditLogs: AuditLogEvent[] = [
    { id: 1, timestamp: '2024-07-29 10:05:12', username: 'admin@kmrl.co.in', action: 'Login', details: 'User logged in successfully from IP 192.168.1.1' },
    { id: 2, timestamp: '2024-07-29 10:06:45', username: 'admin@kmrl.co.in', action: 'Permission Change', details: 'Changed "View All Dept Docs" for "Manager" to true' },
    { id: 3, timestamp: '2024-07-28 15:20:01', username: 'manager.fin@kmrl.co.in', action: 'Document View', details: 'Viewed document ID 3: "Q2 Financial Report Submission"' },
    { id: 4, timestamp: '2024-07-28 15:21:30', username: 'manager.fin@kmrl.co.in', action: 'Document Share', details: 'Shared document ID 1 with staff.legal@kmrl.co.in' },
    { id: 5, timestamp: '2024-07-28 14:00:55', username: 'director.ops@kmrl.co.in', action: 'Login', details: 'User logged in successfully' },
    { id: 6, timestamp: '2024-07-28 11:30:10', username: 'staff.safety@kmrl.co.in', action: 'Document Download', details: 'Downloaded document ID 8: "അറിയിപ്പ്: സുരക്ഷാ ഓഡിറ്റ്"' },
    { id: 7, timestamp: '2024-07-28 09:00:00', username: 'admin@kmrl.co.in', action: 'User Edit', details: 'Updated role for staff.safety@kmrl.co.in to Manager' },
];

const mockSensorData: Sensor[] = [
    { id: 1, name: 'Temperature Sensor', type: 'Temperature', status: 'normal', currentValue: '28.5', unit: '°C', threshold: '35°C', location: 'Aluva Station - Platform 1', lastUpdate: '2m ago', icon: 'fas fa-thermometer-half' },
    { id: 2, name: 'Humidity Sensor', type: 'Humidity', status: 'normal', currentValue: '68', unit: '%', threshold: '80%', location: 'Aluva Station - Concourse', lastUpdate: '1m ago', icon: 'fas fa-tint' },
    { id: 3, name: 'Air Quality Monitor', type: 'Air Quality', status: 'warning', currentValue: '78', unit: 'AQI', threshold: '100AQI', location: 'Ernakulam South - Main Hall', lastUpdate: '30s ago', icon: 'fas fa-wind' },
    { id: 4, name: 'Power Monitor', type: 'Power', status: 'normal', currentValue: '240.1', unit: 'V', threshold: '250V', location: 'Kalamassery Substation', lastUpdate: '5m ago', icon: 'fas fa-bolt' },
    { id: 5, name: 'Emergency Door', type: 'Door Status', status: 'critical', currentValue: 'Open', unit: '', threshold: 'Closed', location: 'CUSAT Tunnel Exit', lastUpdate: '10s ago', icon: 'fas fa-door-open' },
    { id: 6, name: 'Motion Detector', type: 'Motion', status: 'normal', currentValue: 'None', unit: '', threshold: 'N/A', location: 'Pulinchodu - Staff Area', lastUpdate: '8m ago', icon: 'fas fa-walking' },
];


const languages = [
    "English", "Hindi", "Assamese", "Bengali", "Gujarati", "Kannada", "Kashmiri", "Konkani",
    "Malayalam", "Manipuri", "Marathi", "Nepali", "Oriya", "Punjabi", "Sanskrit", "Sindhi",
    "Tamil", "Telugu", "Urdu", "Bodo", "Santhali", "Maithili", "Dogri"
];

const departmentColors: Record<Department, string> = {
    'Operations': 'var(--dept-ops)', 'HR': 'var(--dept-hr)', 'Finance': 'var(--dept-fin)',
    'Legal': 'var(--dept-legal)', 'IT': 'var(--dept-it)', 'Safety': 'var(--priority-high)', 
    'Engineering': '#6c757d', 'Maintenance': '#17a2b8', 'All': '#6c757d'
};

const departmentEmojis: Record<Department, string> = {
    'Operations': '🚇', 'HR': '👥', 'Finance': '💰', 'Legal': '⚖️',
    'IT': '💻', 'Safety': '🛡️', 'Engineering': '⚙️', 'Maintenance': '🔧', 'All': '🏢'
};

const sourceIcons: Record<DocSource, string> = {
    'Email': 'fas fa-envelope',
    'SharePoint': 'fab fa-windows',
    'Scanned': 'fas fa-scanner',
    'Maximo': 'fas fa-cogs',
    'Web Dashboard': 'fas fa-desktop',
};


const priorityColors: Record<Priority, string> = {
    'High': 'var(--priority-high)', 'Medium': 'var(--priority-medium)', 'Low': 'var(--priority-low)'
};

const allRoles: Role[] = ['Staff', 'Manager', 'Director', 'Board Member', 'Admin'];
const allDepartments: Department[] = ['HR', 'Finance', 'Engineering', 'Safety', 'Legal', 'Operations', 'Maintenance', 'IT'];
const allDocTypes: DocType[] = ['Schedule', 'Policy', 'Report', 'Contract', 'Notice', 'Audit', 'Claim', 'Research'];
const allPriorities: Priority[] = ['Low', 'Medium', 'High'];


// --- API CLIENT ---
const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });

// --- CONTEXT for User Management ---
const AuthContext = createContext<{ user: User | null; logout: () => void; } | null>(null);
const useAuth = () => useContext(AuthContext);

// --- HELPER FUNCTIONS ---
const delay = (ms: number) => new Promise(res => setTimeout(res, ms));

// --- COMPONENTS ---
const LoginPage: React.FC<{ onLogin: (user: User) => void }> = ({ onLogin }) => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const handleLogin = (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);

        setTimeout(() => { // Simulate network delay
            const userDetails = mockUsers[username.toLowerCase()];
            if (userDetails && userDetails.password === password) {
                onLogin({ username, role: userDetails.role, department: userDetails.department });
            } else {
                setError('Invalid username or password.');
            }
            setIsLoading(false);
        }, 1000);
    };

    return (
        <div className="login-page">
            <div className="login-container">
                <div className="login-branding">
                    <div className="login-logo">KMRL</div>
                    <h1>Welcome to the Document Intelligence Platform</h1>
                    <p>Empowering decisions with intelligent data.</p>
                </div>
                <div className="login-box">
                    <>
                        <h2>Sign In</h2>
                        <p className="login-subtitle">Enter your credentials to access the dashboard.</p>
                        <form onSubmit={handleLogin}>
                            <div className="input-group">
                                <i className="fas fa-user"></i>
                                <input
                                    type="text"
                                    id="username"
                                    placeholder="e.g., admin@kmrl.co.in"
                                    value={username}
                                    onChange={e => setUsername(e.target.value)}
                                    required
                                    autoCapitalize="none"
                                />
                            </div>
                            <div className="input-group">
                                <i className="fas fa-lock"></i>
                                <input
                                    type="password"
                                    id="password"
                                    placeholder="Password"
                                    value={password}
                                    onChange={e => setPassword(e.target.value)}
                                    required
                                />
                            </div>
                            {error && <div className="login-error">{error}</div>}
                            <button type="submit" className="login-btn" disabled={isLoading}>
                                {isLoading ? 'Signing In...' : 'Sign In'}
                            </button>
                        </form>
                        <div className="forgot-password">
                            <a href="#">Forgot Password?</a>
                        </div>
                    </>
                </div>
            </div>
        </div>
    );
};

const NotificationDropdown: React.FC<{ notifications: Document[] }> = ({ notifications }) => {
    if (notifications.length === 0) {
        return <div className="notification-menu empty">No new alerts.</div>;
    }
    return (
        <div className="notification-menu">
            <div className="notification-header">Compliance Alerts</div>
            {notifications.map(doc => (
                <div key={doc.id} className="notification-item">
                    <div className="notification-dept" style={{borderColor: departmentColors[doc.departments[0]]}}>{departmentEmojis[doc.departments[0]]} {doc.departments[0]}</div>
                    <div className="notification-content">
                        <strong>{doc.subject}</strong>
                        <p>From: {doc.sender}</p>
                    </div>
                </div>
            ))}
        </div>
    );
};

const Header: React.FC<{ toggleSidebar: () => void, onSearch: (term: string) => void, notifications: Document[] }> = ({ toggleSidebar, onSearch, notifications }) => {
    const { user, logout } = useAuth();
    const [profileOpen, setProfileOpen] = useState(false);
    const [notificationsOpen, setNotificationsOpen] = useState(false);

    return (
        <header className="header">
            <div className="header-left">
                <button onClick={toggleSidebar} className="menu-toggle" aria-label="Toggle sidebar"><i className="fas fa-bars"></i></button>
                <div className="search-bar">
                    <i className="fas fa-search"></i>
                    <input type="text" placeholder="Semantic search for documents, policies..." onChange={(e) => onSearch(e.target.value)} />
                </div>
            </div>
            <div className="header-right">
                <div className="notification-bell" onClick={() => setNotificationsOpen(!notificationsOpen)}>
                    <i className="fas fa-bell"></i>
                    {notifications.length > 0 && <span className="notification-badge">{notifications.length}</span>}
                    {notificationsOpen && <NotificationDropdown notifications={notifications} />}
                </div>
                <div className="profile-dropdown" onClick={() => setProfileOpen(!profileOpen)}>
                    <div className="profile-info">
                        <i className="fas fa-user-circle"></i>
                        <span>{user?.role}</span>
                        <i className={`fas fa-chevron-down ${profileOpen ? 'open' : ''}`}></i>
                    </div>
                    {profileOpen && (
                        <div className="dropdown-menu">
                            <button onClick={logout}>
                                <i className="fas fa-sign-out-alt"></i> Logout
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </header>
    );
};

const Sidebar: React.FC<{ isOpen: boolean; activeView: string; setActiveView: (view: string) => void; activeDept: string; setActiveDept: (dept: string) => void;}> = ({ isOpen, activeView, setActiveView, activeDept, setActiveDept }) => {
    const { user } = useAuth();

    const accessibleDepartments: Department[] = useMemo(() => {
        if (!user) return [];
        if (user.role === 'Admin' || user.role === 'Board Member') {
            return allDepartments.filter(d => d !== 'All' && d !== 'Engineering' && d !== 'Maintenance'); // temp filter for demo
        }
        return [user.department];
    }, [user]);

    return (
        <aside className={`sidebar ${isOpen ? 'open' : 'collapsed'}`}>
            <div className="sidebar-header">KMRL Intel</div>
            <nav>
                <ul className="sidebar-nav">
                    <li><a href="#" className={activeView === 'Dashboard' ? 'active' : ''} onClick={() => setActiveView('Dashboard')}><i className="fas fa-tachometer-alt"></i> Dashboard</a></li>
                    <li><a href="#" className={activeView === 'Sensors' ? 'active' : ''} onClick={() => setActiveView('Sensors')}><i className="fas fa-broadcast-tower"></i> IoT Sensors</a></li>
                    <li><a href="#" className={activeView === 'Compliance' ? 'active' : ''} onClick={() => setActiveView('Compliance')}><i className="fas fa-exclamation-triangle"></i> Compliance Alerts</a></li>
                    <li><a href="#" className={activeView === 'Knowledge' ? 'active' : ''} onClick={() => setActiveView('Knowledge')}><i className="fas fa-book"></i> Knowledge Hub</a></li>
                    {user?.role === 'Admin' && (
                       <>
                        <li><a href="#" className={activeView === 'Permissions' ? 'active' : ''} onClick={() => setActiveView('Permissions')}><i className="fas fa-shield-alt"></i> User Management</a></li>
                        <li><a href="#" className={activeView === 'AuditLogs' ? 'active' : ''} onClick={() => setActiveView('AuditLogs')}><i className="fas fa-history"></i> Audit Logs</a></li>
                       </>
                    )}
                    <li><a href="#" className={activeView === 'Settings' ? 'active' : ''} onClick={() => setActiveView('Settings')}><i className="fas fa-cog"></i> Settings</a></li>
                </ul>
            </nav>
            {accessibleDepartments.length > 1 && (
                <div className="sidebar-departments">
                    <h4>Departments</h4>
                    <ul>
                        <li>
                            <button className={activeDept === 'All' ? 'active' : ''} onClick={() => setActiveDept('All')}>
                                <span className="dept-color-tag" style={{ backgroundColor: '#6c757d' }}></span> {departmentEmojis['All']} All Departments
                            </button>
                        </li>
                        {accessibleDepartments.map(dept => (
                            <li key={dept}>
                                <button className={activeDept === dept ? 'active' : ''} onClick={() => setActiveDept(dept)}>
                                    <span className="dept-color-tag" style={{ backgroundColor: departmentColors[dept] }}></span> {departmentEmojis[dept]} {dept}
                                </button>
                            </li>
                        ))}
                    </ul>
                </div>
            )}
        </aside>
    );
};

const DocumentCard: React.FC<{ doc: Document; onViewSummary: (doc: Document) => void; onShareDoc: (doc: Document) => void; }> = ({ doc, onViewSummary, onShareDoc }) => {
    const [summaryLang, setSummaryLang] = useState<'en' | 'ml'>('en');

    const handleDownload = () => {
        if (doc.attachmentFilename) {
            const blob = new Blob([doc.body], { type: 'text/plain;charset=utf-8' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            // Create a .txt filename from the original to represent downloading the body
            const txtFilename = doc.attachmentFilename.substring(0, doc.attachmentFilename.lastIndexOf('.')) + '.txt';
            a.download = txtFilename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        } else {
            alert('No attachment available for this document.');
        }
    };
    
    const summaryText = summaryLang === 'en' ? doc.summary.en : doc.summary.ml;

    return (
        <div className={`document-card ${doc.critical ? 'alert-card-item' : ''}`}>
            <div className="card-header">
                <div>
                  <span className="department-tag" style={{ backgroundColor: departmentColors[doc.departments[0]] }}><i className={sourceIcons[doc.source]}></i> {doc.departments.join(', ')}</span>
                  <span className="doctype-tag">{doc.docType}</span>
                </div>
                <span className="priority-tag" style={{ backgroundColor: priorityColors[doc.priority] }}>{doc.priority}</span>
            </div>
            <div className="card-body">
                <h4>{doc.subject}</h4>
                <div className="card-meta">
                    <span><strong>From:</strong> {doc.sender}</span>
                    <span><strong>Date:</strong> {doc.date}</span>
                </div>
                <div className="summary-container">
                    <p className={`card-summary ${!summaryText ? 'loading' : ''} ${doc.summaryError ? 'error' : ''}`}>
                        {summaryText || (doc.summaryError ? "Could not generate summary..." : "Generating summary...")}
                    </p>
                    <div className="summary-toggle">
                        <button onClick={() => setSummaryLang('en')} className={summaryLang === 'en' ? 'active' : ''}>EN</button>
                        <button onClick={() => setSummaryLang('ml')} className={summaryLang === 'ml' ? 'active' : ''}>ML</button>
                    </div>
                </div>
            </div>
            <div className="card-footer">
                <button className="card-btn" onClick={handleDownload}><i className="fas fa-file-download"></i> Download</button>
                <div className="card-footer-actions">
                    <button className="card-btn share" onClick={() => onShareDoc(doc)}><i className="fas fa-share-alt"></i> Share</button>
                    <button className="card-btn primary" onClick={() => onViewSummary(doc)}>View Details</button>
                </div>
            </div>
        </div>
    );
};

const ShareDocumentModal: React.FC<{
    doc: Document;
    onClose: () => void;
    onShare: (sharedWithUsernames: string[]) => void;
}> = ({ doc, onClose, onShare }) => {
    const { user: currentUser } = useAuth();
    const allPossibleUsers = Object.keys(mockUsers)
        .filter(u => !['admin', 'board'].includes(u) && u !== currentUser?.username);
        
    const [selectedUsers, setSelectedUsers] = useState<Set<string>>(new Set(doc.sharedWith || []));

    const handleUserToggle = (username: string) => {
        const newSelection = new Set(selectedUsers);
        if (newSelection.has(username)) {
            newSelection.delete(username);
        } else {
            newSelection.add(username);
        }
        setSelectedUsers(newSelection);
    };

    const handleShare = (e: React.FormEvent) => {
        e.preventDefault();
        onShare(Array.from(selectedUsers));
    };

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content" onClick={e => e.stopPropagation()}>
                <form onSubmit={handleShare} className="modal-form">
                    <div className="modal-header">
                        <h2>Share "{doc.subject}"</h2>
                        <button type="button" className="modal-close-btn" onClick={onClose} aria-label="Close modal"><i className="fas fa-times"></i></button>
                    </div>
                    <div className="modal-body">
                        <div className="form-group full-width">
                            <label>Select users to share this document with:</label>
                            <div className="user-list-container">
                                <ul className="user-list">
                                    {allPossibleUsers.map(username => (
                                        <li key={username}>
                                            <label>
                                                <input
                                                    type="checkbox"
                                                    checked={selectedUsers.has(username)}
                                                    onChange={() => handleUserToggle(username)}
                                                />
                                                <span>{username}</span>
                                            </label>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        </div>
                    </div>
                    <div className="modal-footer">
                        <button type="button" className="card-btn" onClick={onClose}>Cancel</button>
                        <button type="submit" className="card-btn share"><i className="fas fa-share-alt"></i> Share</button>
                    </div>
                </form>
            </div>
        </div>
    );
};


const DocumentModal: React.FC<{ doc: Document; onClose: () => void; onShareDoc: (doc: Document) => void; }> = ({ doc, onClose, onShareDoc }) => {
    const [activeSummaryRole, setActiveSummaryRole] = useState<Role>('Manager');
    const [targetLang, setTargetLang] = useState('Original');
    const [translatedBody, setTranslatedBody] = useState('');
    const [isTranslating, setIsTranslating] = useState(false);
    const [translationError, setTranslationError] = useState('');


    const handleDownloadOriginal = () => {
         if (doc.attachmentFilename) {
            const blob = new Blob([doc.body], { type: 'text/plain;charset=utf-8' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            const txtFilename = doc.attachmentFilename.substring(0, doc.attachmentFilename.lastIndexOf('.')) + '.txt';
            a.download = txtFilename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        } else {
            alert('No original file available for this document.');
        }
    }

    const handleTranslate = async (lang: string) => {
        if (lang === 'Original') {
            setTargetLang('Original');
            setTranslatedBody('');
            setTranslationError('');
            return;
        }

        setTargetLang(lang);
        setIsTranslating(true);
        setTranslationError('');
        setTranslatedBody('');

        try {
            const prompt = `Translate the following text accurately into ${lang}: "${doc.body}"`;
            const result = await ai.models.generateContent({
                model: 'gemini-2.5-flash',
                contents: prompt,
            });
            setTranslatedBody(result.text.trim());
        } catch (error) {
            console.error(`Error translating to ${lang}:`, error);
            setTranslationError(`Failed to translate text to ${lang}. Please try again.`);
        } finally {
            setIsTranslating(false);
        }
    };

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content" onClick={e => e.stopPropagation()}>
                <div className="modal-header">
                    <h2>{doc.subject}</h2>
                    <button className="modal-close-btn" onClick={onClose} aria-label="Close modal"><i className="fas fa-times"></i></button>
                </div>
                <div className="modal-body">
                    <div className="modal-details-grid">
                        <div className="detail-item"><h5>From</h5><p>{doc.sender}</p></div>
                        <div className="detail-item"><h5>Source</h5><p><i className={sourceIcons[doc.source]}></i> {doc.source}</p></div>
                        <div className="detail-item"><h5>Department</h5><p>{departmentEmojis[doc.departments[0]]} {doc.departments.join(', ')}</p></div>
                        <div className="detail-item"><h5>Document Type</h5><p>{doc.docType}</p></div>
                    </div>
                    <div className="modal-section">
                        <h4>Role-Specific Summaries</h4>
                        <div className="management-tabs summary-tabs">
                             <button onClick={() => setActiveSummaryRole('Staff')} className={activeSummaryRole === 'Staff' ? 'active' : ''}>For Staff</button>
                             <button onClick={() => setActiveSummaryRole('Manager')} className={activeSummaryRole === 'Manager' ? 'active' : ''}>For Manager</button>
                             <button onClick={() => setActiveSummaryRole('Director')} className={activeSummaryRole === 'Director' ? 'active' : ''}>For Director</button>
                        </div>
                        <p className="modal-summary-text">{doc.roleSpecificSummaries[activeSummaryRole]}</p>
                    </div>
                    <div className="modal-section">
                        <div className="section-header-controls">
                           <h4>Original Message</h4>
                           <div className="translator-controls">
                                <span>Translate to:</span>
                                <button onClick={() => handleTranslate('Original')} className={targetLang === 'Original' ? 'active' : ''}>Original</button>
                                <button onClick={() => handleTranslate('English')} className={targetLang === 'English' ? 'active' : ''}>English</button>
                                <button onClick={() => handleTranslate('Malayalam')} className={targetLang === 'Malayalam' ? 'active' : ''}>Malayalam</button>
                                <button onClick={() => handleTranslate('Hindi')} className={targetLang === 'Hindi' ? 'active' : ''}>Hindi</button>
                           </div>
                        </div>
                        <div className="modal-body-text">
                            {isTranslating && <p><i>Translating...</i></p>}
                            {translationError && <p className="error-text"><i>{translationError}</i></p>}
                            {!isTranslating && !translationError && (
                                targetLang === 'Original' ? doc.body : translatedBody
                            )}
                        </div>
                    </div>
                </div>
                <div className="modal-footer">
                     <button className="card-btn" onClick={handleDownloadOriginal}><i className="fas fa-file-download"></i> Download Original</button>
                     <button className="card-btn share" onClick={() => onShareDoc(doc)}><i className="fas fa-share-alt"></i> Share</button>
                </div>
            </div>
        </div>
    );
};

const AddDocumentModal: React.FC<{ onClose: () => void; onSubmit: (data: Partial<Document>) => void; }> = ({ onClose, onSubmit }) => {
    const { user } = useAuth();
    const [title, setTitle] = useState('');
    const [priority, setPriority] = useState<Priority>('Medium');
    const [description, setDescription] = useState('');
    const [file, setFile] = useState<File | null>(null);
    const [selectedDepartments, setSelectedDepartments] = useState<Set<Department>>(new Set());
    const [expiresIn, setExpiresIn] = useState('30 days');

    const handleDepartmentChange = (dept: Department) => {
        const newSelection = new Set(selectedDepartments);
        if (newSelection.has(dept)) {
            newSelection.delete(dept);
        } else {
            newSelection.add(dept);
        }
        setSelectedDepartments(newSelection);
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!title || !file || selectedDepartments.size === 0) {
            alert('Please fill out all required fields: File, Title, and at least one Department.');
            return;
        }
        onSubmit({
            subject: title,
            sender: user?.username || 'unknown@kmrl.co.in',
            departments: Array.from(selectedDepartments),
            priority,
            body: description,
            source: 'Web Dashboard',
            attachmentFilename: file?.name,
            docType: 'Report', // Default for now
            accessExpiresIn: expiresIn
        });
    };
    
    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files.length > 0) {
            setFile(e.target.files[0]);
            if (!title) {
                setTitle(e.target.files[0].name.replace(/\.[^/.]+$/, ""));
            }
        }
    };

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content large" onClick={e => e.stopPropagation()}>
                <form onSubmit={handleSubmit} className="modal-form">
                    <div className="modal-header">
                        <h2><i className="fas fa-upload"></i> Share New File</h2>
                        <button type="button" className="modal-close-btn" onClick={onClose} aria-label="Close modal"><i className="fas fa-times"></i></button>
                    </div>
                    <div className="modal-body">
                        <div className="form-group full-width">
                            <label htmlFor="file-upload">Select File</label>
                            <div className="custom-file-input">
                                <label htmlFor="file-upload" className="file-input-label">
                                    Choose File
                                </label>
                                <span className="file-input-text">{file ? file.name : 'No file chosen'}</span>
                                <input id="file-upload" type="file" onChange={handleFileChange} style={{ display: 'none' }} required />
                            </div>
                        </div>
                        <div className="share-form-grid">
                            <div className="form-group">
                                <label htmlFor="title">File Title</label>
                                <input id="title" type="text" value={title} onChange={e => setTitle(e.target.value)} required placeholder="Enter file title..." />
                            </div>
                            <div className="form-group">
                                <label htmlFor="priority">Priority</label>
                                <select id="priority" value={priority} onChange={e => setPriority(e.target.value as Priority)} required>
                                    {allPriorities.map(p => <option key={p} value={p}>{p}</option>)}
                                </select>
                            </div>
                        </div>
                        <div className="form-group full-width">
                            <label htmlFor="description">Note</label>
                            <textarea id="description" value={description} onChange={e => setDescription(e.target.value)} placeholder="Note details to be shared..." />
                        </div>
                        <div className="departments-container">
                            <h5>Share with Departments</h5>
                            <div className="departments-grid">
                                {allDepartments.map(dept => (
                                    <label key={dept} className="department-checkbox">
                                        <input
                                            type="checkbox"
                                            checked={selectedDepartments.has(dept)}
                                            onChange={() => handleDepartmentChange(dept)}
                                        />
                                        <span>{dept}</span>
                                    </label>
                                ))}
                            </div>
                        </div>
                        <div className="form-group full-width">
                            <label htmlFor="expiresIn">Access Expires In</label>
                            <select id="expiresIn" value={expiresIn} onChange={e => setExpiresIn(e.target.value)} required>
                                <option value="7 days">7 days</option>
                                <option value="30 days">30 days</option>
                                <option value="90 days">90 days</option>
                                <option value="Never">Never</option>
                            </select>
                        </div>
                    </div>
                    <div className="modal-footer">
                         <button type="button" className="card-btn" onClick={onClose}>Cancel</button>
                         <button type="submit" className="card-btn share"><i className="fas fa-share-alt"></i> Share File</button>
                    </div>
                </form>
            </div>
        </div>
    );
};

const DashboardView: React.FC<{ documents: Document[], onViewDoc: (doc: Document) => void; onActionClick: (action: string) => void; onAddNew: () => void; onShareDoc: (doc: Document) => void; }> = ({ documents, onViewDoc, onActionClick, onAddNew, onShareDoc }) => {
    const { user } = useAuth();
    const quickActions: Record<Role, { icon: string; label: string }[]> = {
        'Staff': [{ icon: 'fas fa-search', label: 'View & Search' }],
        'Manager': [{ icon: 'fas fa-check-double', label: 'Approve Documents' }, { icon: 'fas fa-share-square', label: 'Forward Items' }],
        'Director': [{ icon: 'fas fa-chart-pie', label: 'Cross-Dept Analytics' }, { icon: 'fas fa-tasks', label: 'Track Approvals' }],
        'Admin': [{ icon: 'fas fa-users-cog', label: 'Manage Users & Roles' }, { icon: 'fas fa-cogs', label: 'System Settings' }, { icon: 'fas fa-history', label: 'Full Audit Logs' }],
        'Board Member': [],
    };

    const userActions = user ? quickActions[user.role] : [];
    
    const handleActionKeyPress = (e: React.KeyboardEvent, label: string) => {
        if (e.key === 'Enter' || e.key === ' ') {
            onActionClick(label);
        }
    };

    return (
        <>
            <div className="content-header">
                <h1>Dashboard</h1>
                <button className="add-doc-btn" onClick={onAddNew}>
                    <i className="fas fa-share-alt"></i> Share New File
                </button>
            </div>
            
            <div className="dashboard-main-content">
                {userActions.length > 0 && (
                    <section className="quick-actions">
                        {userActions.map(action => (
                            <div 
                                className="action-card" 
                                key={action.label}
                                onClick={() => onActionClick(action.label)}
                                onKeyPress={(e) => handleActionKeyPress(e, action.label)}
                                role="button"
                                tabIndex={0}
                            >
                                <i className={action.icon}></i>
                                <h3>{action.label}</h3>
                            </div>
                        ))}
                    </section>
                )}
                <section>
                    <h2 className="section-header">Recent Documents</h2>
                    <div className="documents-grid">
                        {documents.length > 0 ? (
                            documents.map(doc => (
                                <DocumentCard key={doc.id} doc={doc} onViewSummary={onViewDoc} onShareDoc={onShareDoc} />
                            ))
                        ) : (
                            <p>No recent documents found.</p>
                        )}
                    </div>
                </section>
            </div>
        </>
    );
}

const EditUserModal: React.FC<{ user: User; onClose: () => void; onSave: (user: User) => void }> = ({ user, onClose, onSave }) => {
    const [role, setRole] = useState(user.role);
    const [department, setDepartment] = useState(user.department);
    const availableRoles: Role[] = ['Staff', 'Manager', 'Director', 'Board Member', 'Admin'];

    const handleSave = (e: React.FormEvent) => {
        e.preventDefault();
        onSave({ ...user, role, department });
    };

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content" onClick={e => e.stopPropagation()}>
                <form onSubmit={handleSave} className="modal-form">
                    <div className="modal-header">
                        <h2>Edit User: {user.username}</h2>
                        <button type="button" className="modal-close-btn" onClick={onClose} aria-label="Close modal"><i className="fas fa-times"></i></button>
                    </div>
                    <div className="modal-body">
                        <div className="form-grid">
                            <div className="form-group full-width">
                                <label htmlFor="role">Role</label>
                                <select id="role" value={role} onChange={e => setRole(e.target.value as Role)}>
                                    {availableRoles.map(r => <option key={r} value={r}>{r}</option>)}
                                </select>
                            </div>
                            <div className="form-group full-width">
                                <label htmlFor="department">Department</label>
                                <select id="department" value={department} onChange={e => setDepartment(e.target.value as Department)}>
                                    {[...allDepartments, 'All'].map(d => <option key={d} value={d}>{d}</option>)}
                                </select>
                            </div>
                        </div>
                    </div>
                    <div className="modal-footer">
                        <button type="button" className="card-btn" onClick={onClose}>Cancel</button>
                        <button type="submit" className="card-btn primary">Save Changes</button>
                    </div>
                </form>
            </div>
        </div>
    );
};

const UserManagementView: React.FC<{
    users: User[];
    permissions: Record<string, Record<EditableRole, boolean>>;
    onUpdateUser: (user: User) => void;
    onUpdatePermission: (feature: string, role: EditableRole, value: boolean) => void;
    onBack: () => void;
}> = ({ users, permissions, onUpdateUser, onUpdatePermission, onBack }) => {
    const [activeTab, setActiveTab] = useState<'users' | 'roles'>('users');
    const [userToEdit, setUserToEdit] = useState<User | null>(null);

    const editableRoles: EditableRole[] = ['Staff', 'Manager', 'Director'];
    const features = Object.keys(permissions);

    return (
        <div className="demo-view">
            <div className="content-header">
                <h1>User & Role Management</h1>
                 <button onClick={onBack} className="back-button"><i className="fas fa-arrow-left"></i> Back to Dashboard</button>
            </div>
            <div className="demo-table-container">
                <div className="management-tabs">
                    <button className={activeTab === 'users' ? 'active' : ''} onClick={() => setActiveTab('users')}>
                        <i className="fas fa-users"></i> Manage Users
                    </button>
                    <button className={activeTab === 'roles' ? 'active' : ''} onClick={() => setActiveTab('roles')}>
                        <i className="fas fa-user-shield"></i> Manage Role Permissions
                    </button>
                </div>
                <div className="management-content">
                    {activeTab === 'users' && (
                        <table className="management-table">
                            <thead>
                                <tr>
                                    <th>Username</th>
                                    <th>Role</th>
                                    <th>Department</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {users.map(user => (
                                    <tr key={user.username}>
                                        <td>{user.username}</td>
                                        <td>{user.role}</td>
                                        <td>{user.department}</td>
                                        <td>
                                            <button className="action-btn edit" onClick={() => setUserToEdit(user)} aria-label={`Edit user ${user.username}`}>
                                                <i className="fas fa-pencil-alt"></i> Edit
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                    {activeTab === 'roles' && (
                        <table className="management-table permissions-table">
                            <thead>
                                <tr>
                                    <th>Feature</th>
                                    {editableRoles.map(role => <th key={role}>{role}</th>)}
                                </tr>
                            </thead>
                            <tbody>
                                {features.map(feature => (
                                    <tr key={feature}>
                                        <td>{feature}</td>
                                        {editableRoles.map(role => (
                                            <td key={role}>
                                                <input
                                                    type="checkbox"
                                                    className="permission-checkbox"
                                                    checked={permissions[feature][role]}
                                                    onChange={(e) => onUpdatePermission(feature, role, e.target.checked)}
                                                    aria-label={`${feature} permission for ${role}`}
                                                />
                                            </td>
                                        ))}
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>
            </div>
            {userToEdit && (
                <EditUserModal
                    user={userToEdit}
                    onClose={() => setUserToEdit(null)}
                    onSave={(updatedUser) => {
                        onUpdateUser(updatedUser);
                        setUserToEdit(null);
                    }}
                />
            )}
        </div>
    );
};

const KnowledgeHubView: React.FC<{ documents: Document[]; onBack: () => void; }> = ({ documents, onBack }) => {
    // Sort documents by due date, with ones without a date at the end
    const sortedDocuments = [...documents].sort((a, b) => {
        if (a.dueDate && b.dueDate) return new Date(a.dueDate).getTime() - new Date(b.dueDate).getTime();
        if (a.dueDate) return -1;
        if (b.dueDate) return 1;
        return 0;
    });

    const formatDate = (dateString?: string) => {
        if (!dateString) return 'N/A';
        return new Date(dateString).toLocaleDateString('en-GB', {
            day: '2-digit',
            month: 'short',
            year: 'numeric'
        });
    };

    return (
        <div className="demo-view">
            <div className="content-header">
                <h1>Knowledge Hub</h1>
                 <button onClick={onBack} className="back-button"><i className="fas fa-arrow-left"></i> Back to Dashboard</button>
            </div>
            <div className="management-content">
                <table className="management-table">
                    <thead>
                        <tr>
                            <th>Document Title</th>
                            <th>Assigned To</th>
                            <th>Priority</th>
                            <th>Doc Type</th>
                            <th>Due Date</th>
                        </tr>
                    </thead>
                    <tbody>
                        {sortedDocuments.length > 0 ? sortedDocuments.map(doc => (
                            <tr key={doc.id}>
                                <td>{doc.subject}</td>
                                <td>{doc.sharedWith && doc.sharedWith.length > 0 ? doc.sharedWith.join(', ') : <span className="unassigned-text">Unassigned</span>}</td>
                                <td><span className="priority-tag" style={{ backgroundColor: priorityColors[doc.priority] }}>{doc.priority}</span></td>
                                <td>{doc.docType}</td>
                                <td className="due-date">{formatDate(doc.dueDate)}</td>
                            </tr>
                        )) : (
                            <tr><td colSpan={5} style={{textAlign: 'center', padding: '20px'}}>No documents found.</td></tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

const DemoView: React.FC<{ action: string; onBack: () => void }> = ({ action, onBack }) => {
    
    const renderDemoContent = () => {
        switch (action) {
            case 'Approve Documents':
            case 'Forward Items':
            case 'Track Approvals':
                return (
                    <div className="demo-table-container">
                        <h3>Pending Documents</h3>
                        <p>This is a demonstration of a document approval workflow. Managers and Directors would see pending items, review them, and then approve, reject, or forward them to other departments.</p>
                        <table className="demo-table">
                            <thead>
                                <tr>
                                    <th><input type="checkbox" aria-label="Select all documents" disabled /></th>
                                    <th>Document Title</th>
                                    <th>From</th>
                                    <th>Received</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td><input type="checkbox" aria-label="Select Q3 Budget Proposal" disabled /></td>
                                    <td>Q3 Budget Proposal</td>
                                    <td>Finance Department</td>
                                    <td>2024-07-28</td>
                                    <td><span className="status-pending">Pending Approval</span></td>
                                </tr>
                                <tr>
                                    <td><input type="checkbox" aria-label="Select New Safety Protocol v2.1" disabled /></td>
                                    <td>New Safety Protocol v2.1</td>
                                    <td>Safety Department</td>
                                    <td>2024-07-27</td>
                                    <td><span className="status-pending">Pending Approval</span></td>
                                </tr>
                                <tr>
                                    <td><input type="checkbox" aria-label="Select Vendor Contract Renewal - XYZ Corp" disabled /></td>
                                    <td>Vendor Contract Renewal - XYZ Corp</td>
                                    <td>Legal Department</td>
                                    <td>2024-07-26</td>
                                    <td><span className="status-approved">Approved</span></td>
                                </tr>
                            </tbody>
                        </table>
                        <div className="demo-actions">
                            <button className="card-btn primary" disabled>Approve Selected</button>
                            <button className="card-btn" disabled>Reject Selected</button>
                            <button className="card-btn" disabled>Forward</button>
                        </div>
                    </div>
                );
            case 'Cross-Dept Analytics':
                return (
                    <div className="demo-analytics-grid">
                         <div className="analytics-card full-width">
                             <h4>Cross-Department Analytics</h4>
                             <p>This analytics dashboard would provide directors with high-level insights into document flow, compliance rates, and processing times across all departments, enabling data-driven strategic decisions.</p>
                        </div>
                        <div className="analytics-card">
                            <h4>Compliance Rate</h4>
                            <div className="analytics-value">98.5%</div>
                            <div className="analytics-chart-placeholder" style={{backgroundColor: 'rgba(0, 136, 90, 0.1)'}}>Chart Placeholder</div>
                        </div>
                        <div className="analytics-card">
                            <h4>Document Processing Time</h4>
                            <div className="analytics-value">1.2 Days</div>
                             <div className="analytics-chart-placeholder" style={{backgroundColor: 'rgba(0, 51, 160, 0.1)'}}>Chart Placeholder</div>
                        </div>
                        <div className="analytics-card full-width">
                             <h4>Documents by Department</h4>
                             <div className="analytics-chart-placeholder" style={{height: '250px'}}>Bar Chart Placeholder</div>
                        </div>
                    </div>
                );
            case 'Compliance Alerts':
                return (
                    <div className="demo-table-container">
                        <h3>Compliance Alerts Dashboard</h3>
                        <p>This screen would provide a detailed view of all critical compliance documents, their status, required actions, and deadlines. Users could filter by department, date, or severity to ensure timely responses.</p>
                        <div className="admin-mockup">Compliance Dashboard Mockup</div>
                    </div>
                );
             case 'Access Denied':
                return (
                    <div className="demo-table-container">
                        <h3>Access Denied</h3>
                        <p>You do not have the necessary permissions to view this page.</p>
                    </div>
                );
            default:
                return <p>This is a demo for the '{action}' feature. In a full application, this screen would provide the tools and interface to perform this action.</p>;
        }
    };

    return (
        <div className="demo-view">
            <div className="content-header">
                <button onClick={onBack} className="back-button"><i className="fas fa-arrow-left"></i> Back to Dashboard</button>
                <h1>Demo: {action}</h1>
            </div>
            {renderDemoContent()}
        </div>
    );
};

const AuditLogView: React.FC<{ onBack: () => void }> = ({ onBack }) => {
    return (
        <div className="demo-view">
            <div className="content-header">
                <h1>Full Audit Logs</h1>
                <button onClick={onBack} className="back-button"><i className="fas fa-arrow-left"></i> Back to Dashboard</button>
            </div>
            <div className="management-content">
                <table className="management-table audit-log-table">
                    <thead>
                        <tr>
                            <th>Timestamp</th>
                            <th>User</th>
                            <th>Action</th>
                            <th>Details</th>
                        </tr>
                    </thead>
                    <tbody>
                        {mockAuditLogs.map(log => (
                            <tr key={log.id}>
                                <td>{log.timestamp}</td>
                                <td>{log.username}</td>
                                <td><span className={`log-action-tag ${log.action.toLowerCase().replace(/ /g, '-')}`}>{log.action}</span></td>
                                <td>{log.details}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

// --- Role-Specific Settings Components ---

const AdminSettings = ({ setChanged }) => (
    <>
        <div className="settings-section">
            <h3><i className="fas fa-users-cog"></i> User Management</h3>
            <div className="settings-item">
                <label>User Actions</label>
                <div className="settings-item-actions">
                    <button className="card-btn" onClick={() => { alert('Navigating to Add User page...'); setChanged(true); }}>Add New User</button>
                    <button className="card-btn" onClick={() => { alert('Navigating to Role Management page...'); setChanged(true); }}>Manage Roles</button>
                </div>
            </div>
        </div>
        <div className="settings-section">
            <h3><i className="fas fa-cogs"></i> System Integrations</h3>
            <div className="settings-item-grid">
                <div className="integration-card">
                    <h4><i className="fab fa-google"></i> Gmail/Outlook</h4>
                    <p>Fetch documents from email inboxes.</p>
                    <button className="card-btn" onClick={() => { alert('Configuring email fetchers...'); setChanged(true); }}>Configure</button>
                </div>
                <div className="integration-card">
                    <h4><i className="fab fa-windows"></i> SharePoint</h4>
                    <p>Sync with SharePoint document libraries.</p>
                    <button className="card-btn" onClick={() => { alert('Configuring SharePoint...'); setChanged(true); }}>Configure</button>
                </div>
                 <div className="integration-card">
                    <h4><i className="fas fa-cogs"></i> Maximo</h4>
                    <p>Connect to Maximo asset management.</p>
                    <button className="card-btn" onClick={() => { alert('Configuring Maximo...'); setChanged(true); }}>Configure</button>
                </div>
                <div className="integration-card">
                    <h4><i className="fas fa-broadcast-tower"></i> IoT Feeds</h4>
                    <p>Connect to sensor and system data feeds.</p>
                    <button className="card-btn" onClick={() => { alert('Configuring IoT feeds...'); setChanged(true); }}>Configure</button>
                </div>
            </div>
        </div>
        <div className="settings-section">
            <h3><i className="fas fa-shield-alt"></i> Audit & Compliance</h3>
            <div className="settings-item">
                <label>Enable Audit Trails</label>
                <label className="switch"><input type="checkbox" defaultChecked onChange={() => setChanged(true)} /><span className="slider round"></span></label>
            </div>
            <div className="settings-item">
                <label>Export Compliance Logs</label>
                <button className="card-btn" onClick={() => { alert('Exporting logs...'); setChanged(true); }}><i className="fas fa-file-export"></i> Export</button>
            </div>
        </div>
        <div className="settings-section">
            <h3><i className="fas fa-database"></i> Backup & Recovery</h3>
             <div className="settings-item">
                <label>System Data Management</label>
                <div className="settings-item-actions">
                    <button className="card-btn" onClick={() => { alert('Exporting data...'); setChanged(true); }}>Export Data</button>
                    <button className="card-btn" onClick={() => { alert('Importing data...'); setChanged(true); }}>Import Data</button>
                </div>
            </div>
        </div>
    </>
);

const BoardMemberSettings = ({ setChanged }) => (
    <>
        <div className="settings-section">
            <h3><i className="fas fa-chart-bar"></i> Dashboard Customization</h3>
            <div className="settings-item">
                <p>Select KPIs to display on your dashboard.</p>
            </div>
            <div className="settings-item-grid checkbox-grid">
                <label><input type="checkbox" defaultChecked onChange={() => setChanged(true)} /> Safety Compliance</label>
                <label><input type="checkbox" defaultChecked onChange={() => setChanged(true)} /> Financial Summaries</label>
                <label><input type="checkbox" onChange={() => setChanged(true)} /> Train Availability</label>
                <label><input type="checkbox" onChange={() => setChanged(true)} /> Project Milestones</label>
            </div>
        </div>
        <div className="settings-section">
            <h3><i className="fas fa-file-invoice"></i> Reports</h3>
            <div className="settings-item">
                <label htmlFor="board-reports">Schedule Automated Board Reports</label>
                <select id="board-reports" defaultValue="monthly" onChange={() => setChanged(true)}>
                    <option value="weekly">Weekly</option>
                    <option value="monthly">Monthly</option>
                    <option value="quarterly">Quarterly</option>
                    <option value="off">Off</option>
                </select>
            </div>
        </div>
        <div className="settings-section">
            <h3><i className="fas fa-bell"></i> Notifications</h3>
            <div className="settings-item">
                <label>Receive only high-priority alerts</label>
                <label className="switch"><input type="checkbox" defaultChecked onChange={() => setChanged(true)} /><span className="slider round"></span></label>
            </div>
        </div>
    </>
);

const DirectorOpsSettings = ({ setChanged }) => (
    <>
        <div className="settings-section">
            <h3><i className="fas fa-tachometer-alt"></i> Operations KPIs</h3>
            <div className="settings-item kpi-input-group">
                <label htmlFor="kpi-rolling-stock">Rolling-Stock Thresholds</label>
                <input id="kpi-rolling-stock" type="range" min="80" max="100" defaultValue="95" onChange={() => setChanged(true)} />
            </div>
            <div className="settings-item kpi-input-group">
                <label htmlFor="kpi-depot">Depot Equipment Availability</label>
                <input id="kpi-depot" type="range" min="80" max="100" defaultValue="90" onChange={() => setChanged(true)} />
            </div>
        </div>
        <div className="settings-section">
            <h3><i className="fas fa-route"></i> Document Routing</h3>
            <div className="settings-item">
                <label>Auto-forward incident reports to Safety & Engineering</label>
                <label className="switch"><input type="checkbox" defaultChecked onChange={() => setChanged(true)} /><span className="slider round"></span></label>
            </div>
        </div>
        <div className="settings-section">
            <h3><i className="fas fa-user-friends"></i> Delegation</h3>
            <div className="settings-item">
                <label htmlFor="delegation">Assign Backup Approver</label>
                <select id="delegation" onChange={() => setChanged(true)}>
                    <option>manager.ops@kmrl.co.in</option>
                    <option>deputy.director.ops@kmrl.co.in</option>
                </select>
            </div>
        </div>
    </>
);

const DirectorHrSettings = ({ setChanged }) => (
     <>
        <div className="settings-section">
            <h3><i className="fas fa-bullhorn"></i> Alerts & Communication</h3>
            <div className="settings-item">
                <label>Auto-route compliance circulars to staff</label>
                <label className="switch"><input type="checkbox" defaultChecked onChange={() => setChanged(true)} /><span className="slider round"></span></label>
            </div>
            <div className="settings-item">
                <label>Enable bilingual notifications for field staff</label>
                <label className="switch"><input type="checkbox" defaultChecked onChange={() => setChanged(true)} /><span className="slider round"></span></label>
            </div>
        </div>
         <div className="settings-section">
            <h3><i className="fas fa-user-shield"></i> Access Control</h3>
            <div className="settings-item">
                 <label>Policy Document Permissions</label>
                 <button className="card-btn" onClick={() => { alert('Opening policy permissions...'); setChanged(true); }}>Control View/Edit</button>
            </div>
        </div>
        <div className="settings-section">
            <h3><i className="fas fa-chart-line"></i> Reports</h3>
             <div className="settings-item">
                 <label>Generate Staff Reports</label>
                 <button className="card-btn" onClick={() => { alert('Generating reports...'); setChanged(true); }}>Generate Reports</button>
            </div>
        </div>
    </>
);


const ManagerFinanceSettings = ({ setChanged }) => (
    <>
        <div className="settings-section">
            <h3><i className="fas fa-filter"></i> Financial Document Filters</h3>
             <div className="settings-item">
                <p>Select document types to display on your dashboard.</p>
            </div>
            <div className="settings-item-grid checkbox-grid">
                <label><input type="checkbox" defaultChecked onChange={() => setChanged(true)} /> Invoices</label>
                <label><input type="checkbox" defaultChecked onChange={() => setChanged(true)} /> Purchase Orders</label>
                <label><input type="checkbox" onChange={() => setChanged(true)} /> Vendor Contracts</label>
                <label><input type="checkbox" onChange={() => setChanged(true)} /> Expense Claims</label>
            </div>
        </div>
        <div className="settings-section">
            <h3><i className="fas fa-exclamation-triangle"></i> Threshold Alerts</h3>
            <div className="settings-item">
                <label htmlFor="exp-threshold">Notify if expenditure crosses limit (INR)</label>
                <input type="number" id="exp-threshold" defaultValue="50000" className="settings-input" onChange={() => setChanged(true)} />
            </div>
        </div>
        <div className="settings-section">
            <h3><i className="fas fa-check-double"></i> Approval Settings</h3>
            <div className="settings-item">
                <label>Enable multi-level approval flow for payments</label>
                <label className="switch"><input type="checkbox" onChange={() => setChanged(true)} /><span className="slider round"></span></label>
            </div>
        </div>
    </>
);

const StaffSettings = ({ setChanged }) => (
     <>
        <div className="settings-section">
            <h3><i className="fas fa-bell"></i> Alert Preferences</h3>
            <div className="settings-item">
                <label>Receive high-priority safety circulars only</label>
                <label className="switch"><input type="checkbox" defaultChecked onChange={() => setChanged(true)} /><span className="slider round"></span></label>
            </div>
        </div>
         <div className="settings-section">
            <h3><i className="fas fa-tv"></i> Shift View</h3>
            <div className="settings-item">
                <label>Show only today’s relevant reports</label>
                <label className="switch"><input type="checkbox" defaultChecked onChange={() => setChanged(true)} /><span className="slider round"></span></label>
            </div>
        </div>
        <div className="settings-section">
            <h3><i className="fas fa-broadcast-tower"></i> IoT Monitoring</h3>
             <div className="settings-item">
                <p>Customize which safety sensors to monitor.</p>
            </div>
            <div className="settings-item-grid checkbox-grid">
                <label><input type="checkbox" defaultChecked onChange={() => setChanged(true)} /> Fire</label>
                <label><input type="checkbox" onChange={() => setChanged(true)} /> Vibration</label>
                <label><input type="checkbox" defaultChecked onChange={() => setChanged(true)} /> Air Quality</label>
            </div>
        </div>
    </>
);


const SettingsView: React.FC<{ onBack: () => void }> = ({ onBack }) => {
    const { user } = useAuth();
    const [settingsChanged, setSettingsChanged] = useState(false);
    const [theme, setTheme] = useState(document.body.classList.contains('dark-mode') ? 'Dark' : 'Light');

    const handleSave = () => {
        alert('Settings saved successfully!');
        setSettingsChanged(false);
    };

    const handleReset = () => {
        alert('Settings have been reset to default values.');
        // In a real app, you would reset all state variables to their defaults here
        setSettingsChanged(true); // Mark as changed to allow saving
    };

    const handleThemeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const newTheme = e.target.checked ? 'Dark' : 'Light';
        setTheme(newTheme);
        if (e.target.checked) {
            document.body.classList.add('dark-mode');
        } else {
            document.body.classList.remove('dark-mode');
        }
        setSettingsChanged(true);
    };

    const renderRoleSettings = () => {
        switch (user?.role) {
            case 'Admin':
                return <AdminSettings setChanged={setSettingsChanged} />;
            case 'Board Member':
                return <BoardMemberSettings setChanged={setSettingsChanged} />;
            case 'Director':
                if (user.department === 'Operations') return <DirectorOpsSettings setChanged={setSettingsChanged} />;
                if (user.department === 'HR') return <DirectorHrSettings setChanged={setSettingsChanged} />;
                return <p>No specific settings for this director role.</p>;
            case 'Manager':
                if (user.department === 'Finance') return <ManagerFinanceSettings setChanged={setSettingsChanged} />;
                return <p>No specific settings for this manager role.</p>;
            case 'Staff':
                return <StaffSettings setChanged={setSettingsChanged} />;
            default:
                return <div className="settings-section"><p>No settings available for your role.</p></div>;
        }
    };

    return (
        <div className="demo-view">
            <div className="content-header">
                <h1>Settings</h1>
                <button onClick={onBack} className="back-button"><i className="fas fa-arrow-left"></i> Back to Dashboard</button>
            </div>
            <div className="settings-container">
                <div className="settings-section">
                    <h3><i className="fas fa-paint-brush"></i> Appearance</h3>
                    <div className="settings-item">
                        <label htmlFor="theme">Dark Mode</label>
                        <label className="switch">
                            <input id="theme" type="checkbox" onChange={handleThemeChange} checked={theme === 'Dark'} />
                            <span className="slider round"></span>
                        </label>
                    </div>
                </div>
                
                 <div className="settings-section">
                    <h3><i className="fas fa-language"></i> Language</h3>
                     <div className="settings-item">
                        <label htmlFor="language-select">Preferred Summary Language</label>
                        <select id="language-select" defaultValue="english" onChange={() => setSettingsChanged(true)}>
                            <option value="english">English</option>
                            <option value="malayalam">Malayalam</option>
                        </select>
                    </div>
                </div>

                {renderRoleSettings()}

                <div className="settings-footer">
                    <button className="card-btn" onClick={handleReset}>Reset to Defaults</button>
                    <button className="card-btn primary" onClick={handleSave} disabled={!settingsChanged}>
                       {settingsChanged ? 'Save Changes' : 'Saved'}
                    </button>
                </div>
            </div>
        </div>
    );
};


const IoTSensorDashboardView: React.FC<{ sensors: Sensor[]; onBack: () => void }> = ({ sensors, onBack }) => {
    const summary = useMemo(() => {
        return sensors.reduce((acc, sensor) => {
            acc[sensor.status]++;
            return acc;
        }, { normal: 0, warning: 0, critical: 0 });
    }, [sensors]);

    const totalSensors = sensors.length;

    const statusDetails = {
        normal: { icon: 'fas fa-check-circle', color: 'var(--kmrl-green)' },
        warning: { icon: 'fas fa-exclamation-triangle', color: 'var(--priority-medium)' },
        critical: { icon: 'fas fa-exclamation-circle', color: 'var(--priority-high)' },
    };

    return (
        <div className="sensor-dashboard-view">
            <div className="content-header">
                 <div>
                    <h1><i className="fas fa-broadcast-tower"></i> IoT Sensor Dashboard</h1>
                    <p className="dashboard-subtitle">Real-time monitoring of metro infrastructure <span className="online-status"><i className="fas fa-circle"></i> Online</span></p>
                </div>
                 <button onClick={onBack} className="back-button"><i className="fas fa-arrow-left"></i> Back</button>
            </div>

            <div className="sensor-summary-cards">
                <div className="sensor-summary-card">
                    <i className="fas fa-wave-square icon-total"></i>
                    <div>
                        <span className="summary-value">{totalSensors}</span>
                        <span className="summary-label">Total Sensors</span>
                    </div>
                </div>
                <div className="sensor-summary-card">
                    <i className={`${statusDetails.normal.icon} icon-normal`}></i>
                    <div>
                         <span className="summary-value">{summary.normal}</span>
                        <span className="summary-label">Normal</span>
                    </div>
                </div>
                <div className="sensor-summary-card">
                    <i className={`${statusDetails.warning.icon} icon-warning`}></i>
                     <div>
                        <span className="summary-value">{summary.warning}</span>
                        <span className="summary-label">Warning</span>
                    </div>
                </div>
                <div className="sensor-summary-card">
                    <i className={`${statusDetails.critical.icon} icon-critical`}></i>
                     <div>
                        <span className="summary-value">{summary.critical}</span>
                        <span className="summary-label">Critical</span>
                    </div>
                </div>
            </div>

            <div className="sensor-grid">
                {sensors.map(sensor => (
                    <div key={sensor.id} className={`sensor-card status-border-${sensor.status}`}>
                        <div className="sensor-card-header">
                            <div className="sensor-title">
                                <i className={`${sensor.icon} sensor-icon`}></i>
                                <div>
                                    <h4>{sensor.name}</h4>
                                    <span>{sensor.type}</span>
                                </div>
                            </div>
                            <span className={`sensor-status ${sensor.status}`}>
                                {sensor.status}
                            </span>
                        </div>
                        <div className="sensor-card-body">
                            <div className="sensor-value">
                                {sensor.currentValue}<span>{sensor.unit}</span>
                            </div>
                            <div className="sensor-details">
                                <div className="detail-row">
                                    <span>Threshold</span>
                                    <span>{sensor.threshold}</span>
                                </div>
                                <div className="detail-row">
                                    <span>Location</span>
                                    <span>{sensor.location}</span>
                                </div>
                                <div className="detail-row">
                                    <span>Last Update</span>
                                    <span>{sensor.lastUpdate}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};


const DashboardLayout: React.FC = () => {
    const { user } = useAuth();
    const [documents, setDocuments] = useState<Document[]>([]);
    const [filteredDocuments, setFilteredDocuments] = useState<Document[]>([]);
    const [sidebarOpen, setSidebarOpen] = useState(true);
    const [activeView, setActiveView] = useState('Dashboard');
    const [activeDept, setActiveDept] = useState<string>('All');
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedDoc, setSelectedDoc] = useState<Document | null>(null);
    const [docToShare, setDocToShare] = useState<Document | null>(null);
    const [demoAction, setDemoAction] = useState<string | null>(null);
    const [isAddModalOpen, setIsAddModalOpen] = useState(false);
    
    // State for user management
    const [users, setUsers] = useState<User[]>([]);
    const [permissions, setPermissions] = useState(initialPermissions);

    // Initialize users from mock data
     useEffect(() => {
        const initialUsers = Object.entries(mockUsers)
            .filter(([key]) => !['admin', 'board'].includes(key)) // Filter out duplicate shorthand keys
            .map(([username, details]) => ({
                username,
                role: details.role,
                department: details.department,
            }));
        setUsers(initialUsers);
    }, []);


    // Filter initial documents based on user role and set state
    useEffect(() => {
        if (!user) return;
        const userDocs = (user.role === 'Admin' || user.role === 'Board Member' || user.department === 'All')
            ? mockDocuments
            : mockDocuments.filter(doc => doc.departments.includes(user.department) || doc.sharedWith?.includes(user.username));
        
        setDocuments(userDocs.map(doc => ({...doc, summaryError: false})));
    }, [user]);

    // Sequentially generate summaries for documents
    useEffect(() => {
        let isCancelled = false;
        const generateSummaries = async () => {
            const needsSummaries = documents.length > 0 && documents.some(d => !d.summary.en && !d.summary.ml && !d.summaryError);
            if (needsSummaries) {
                const docsToUpdate = [...documents];
                for (let i = 0; i < docsToUpdate.length; i++) {
                    if (isCancelled) break;
                    const doc = docsToUpdate[i];
                    if ((!doc.summary.en && doc.language === 'English') || (!doc.summary.ml && doc.language === 'Malayalam')) {
                        try {
                            const prompt = doc.language === 'English' 
                                ? `Summarize the following text in one concise sentence in English: "${doc.body}"`
                                : `Summarize the following text in one concise sentence in Malayalam: "${doc.body}"`
                            const result = await ai.models.generateContent({
                                model: 'gemini-2.5-flash',
                                contents: prompt,
                            });
                            
                            if (doc.language === 'English') {
                                doc.summary.en = result.text.trim();
                            } else {
                                doc.summary.ml = result.text.trim();
                            }

                        } catch (error) {
                            console.error(`Error generating summary for doc ID ${doc.id}:`, error);
                            doc.summaryError = true;
                        }
                        
                        if (!isCancelled) {
                           setDocuments([...docsToUpdate]); 
                        }

                        await delay(1000); 
                    }
                }
            }
        };
        generateSummaries();
        return () => { isCancelled = true; };
    }, [documents.length]); 

    // Filter documents based on active department and search term
    useEffect(() => {
        let docs = [...documents];
        if (activeDept !== 'All') {
            docs = docs.filter(d => d.departments.includes(activeDept as Department));
        }
        if (searchTerm) {
            const lowercasedTerm = searchTerm.toLowerCase();
            docs = docs.filter(d => 
                d.subject.toLowerCase().includes(lowercasedTerm) ||
                d.sender.toLowerCase().includes(lowercasedTerm) ||
                d.departments.some(dept => dept.toLowerCase().includes(lowercasedTerm)) ||
                (d.summary.en && d.summary.en.toLowerCase().includes(lowercasedTerm)) ||
                (d.summary.ml && d.summary.ml.toLowerCase().includes(lowercasedTerm))
            );
        }
        setFilteredDocuments(docs.filter(doc => !doc.critical)); // Exclude critical docs from main view
    }, [documents, activeDept, searchTerm]);
    
    const userNotifications = useMemo(() => {
       return documents.filter(doc => doc.critical);
    }, [documents]);
    
    const handleSetActiveView = (view: string) => {
        setDemoAction(null);
        setActiveView(view);
    };

    const handleActionClick = (action: string) => {
        switch(action) {
            case 'Manage Users & Roles':
                setActiveView('Permissions');
                break;
            case 'System Settings':
                setActiveView('Settings');
                break;
            case 'Full Audit Logs':
                setActiveView('AuditLogs');
                break;
            default:
                setDemoAction(action);
                break;
        }
    };


    const handleAddDocument = (docData: Partial<Document>) => {
        const newDoc: Document = {
            id: Math.max(0, ...documents.map(d => d.id)) + 1,
            date: new Date().toISOString().split('T')[0],
            language: 'English', // Default for new docs
            critical: docData.priority === 'High',
            summary: { en: '', ml: '' }, // Will be generated
            roleSpecificSummaries: { // Generic placeholders
                Staff: `Review the new document: "${docData.subject}"`,
                Manager: `A new document has been added that requires attention: "${docData.subject}"`,
                Director: `High-level overview of newly ingested document: "${docData.subject}"`,
            },
            summaryError: false,
            sharedWith: [],
            ...docData
        } as Document;

        setDocuments(prevDocs => [newDoc, ...prevDocs]);
        setIsAddModalOpen(false);
    };

    const handleShareDocument = (docId: number, sharedWithUsernames: string[]) => {
        setDocuments(prevDocs => 
            prevDocs.map(doc => 
                doc.id === docId ? { ...doc, sharedWith: sharedWithUsernames } : doc
            )
        );
    };
    
    const handleUpdateUser = (updatedUser: User) => {
        setUsers(users.map(u => u.username === updatedUser.username ? updatedUser : u));
    };

    const handleUpdatePermission = (feature: string, role: EditableRole, value: boolean) => {
        setPermissions(prev => ({
            ...prev,
            [feature]: {
                ...prev[feature],
                [role]: value
            }
        }));
    };

    const renderActiveView = () => {
        if (demoAction) {
            return <DemoView action={demoAction} onBack={() => setDemoAction(null)} />;
        }
        switch (activeView) {
            case 'Dashboard':
                return <DashboardView documents={filteredDocuments} onViewDoc={setSelectedDoc} onActionClick={handleActionClick} onAddNew={() => setIsAddModalOpen(true)} onShareDoc={setDocToShare} />;
            case 'Sensors':
                return <IoTSensorDashboardView sensors={mockSensorData} onBack={() => handleSetActiveView('Dashboard')} />;
            case 'Permissions':
                 if (user?.role !== 'Admin') return <DemoView action="Access Denied" onBack={() => handleSetActiveView('Dashboard')} />;
                return <UserManagementView 
                            users={users} 
                            permissions={permissions} 
                            onUpdateUser={handleUpdateUser}
                            onUpdatePermission={handleUpdatePermission}
                            onBack={() => handleSetActiveView('Dashboard')} 
                        />;
            case 'Compliance':
                return <DemoView action="Compliance Alerts" onBack={() => handleSetActiveView('Dashboard')} />;
            case 'Knowledge':
                return <KnowledgeHubView documents={documents} onBack={() => handleSetActiveView('Dashboard')} />;
            case 'Settings':
                return <SettingsView onBack={() => handleSetActiveView('Dashboard')} />;
            case 'AuditLogs':
                if (user?.role !== 'Admin') return <DemoView action="Access Denied" onBack={() => handleSetActiveView('Dashboard')} />;
                return <AuditLogView onBack={() => handleSetActiveView('Dashboard')} />;
            default:
                 return <DashboardView documents={filteredDocuments} onViewDoc={setSelectedDoc} onActionClick={handleActionClick} onAddNew={() => setIsAddModalOpen(true)} onShareDoc={setDocToShare} />;
        }
    };

    return (
        <div className={`app-layout ${sidebarOpen ? 'sidebar-open' : ''}`}>
            <Sidebar 
                isOpen={sidebarOpen} 
                activeView={activeView} 
                setActiveView={handleSetActiveView}
                activeDept={activeDept}
                setActiveDept={setActiveDept}
            />
            <div className="main-wrapper">
                <Header 
                    toggleSidebar={() => setSidebarOpen(!sidebarOpen)}
                    onSearch={setSearchTerm}
                    notifications={userNotifications}
                />
                <main className="main-content">
                    {renderActiveView()}
                </main>
            </div>
            {selectedDoc && <DocumentModal doc={selectedDoc} onClose={() => setSelectedDoc(null)} onShareDoc={setDocToShare} />}
            {isAddModalOpen && <AddDocumentModal onClose={() => setIsAddModalOpen(false)} onSubmit={handleAddDocument} />}
            {docToShare && (
                <ShareDocumentModal
                    doc={docToShare}
                    onClose={() => setDocToShare(null)}
                    onShare={(sharedWithUsernames) => {
                        handleShareDocument(docToShare.id, sharedWithUsernames);
                        setDocToShare(null);
                    }}
                />
            )}
        </div>
    );
};

// --- MAIN APP COMPONENT ---
const App: React.FC = () => {
    const [user, setUser] = useState<User | null>(() => {
        const savedUser = sessionStorage.getItem('user');
        return savedUser ? JSON.parse(savedUser) : null;
    });

    useEffect(() => {
        if (user) {
            sessionStorage.setItem('user', JSON.stringify(user));
        } else {
            sessionStorage.removeItem('user');
        }
    }, [user]);

    const handleLogin = (loggedInUser: User) => {
        setUser(loggedInUser);
    };

    const handleLogout = () => {
        setUser(null);
    };

    return (
        <AuthContext.Provider value={{ user, logout: handleLogout }}>
            {user ? <DashboardLayout /> : <LoginPage onLogin={handleLogin} />}
        </AuthContext.Provider>
    );
};

const root = createRoot(document.getElementById('root')!);
root.render(<App />);