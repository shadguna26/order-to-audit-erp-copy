import React, { useState } from 'react';
import { LogIn, UserPlus, KeyRound, CheckCircle2, AlertCircle, ArrowRight, ShieldCheck, Sun, Moon, Sparkles } from 'lucide-react';
import { loginUser, registerUser, resetPassword } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { KolamDivider } from '../components/KolamDivider';
import { TwinkleCanvas } from '../components/TwinkleCanvas';
import { GuideHelper } from '../components/GuideHelper';

type AuthMode = 'login' | 'register' | 'forgot';

export const Login: React.FC = () => {
  const { login } = useAuth();
  const { theme, toggleTheme, language, changeLanguage, animationsAndGuides, toggleAnimationsAndGuides } = useTheme();
  const [mode, setMode] = useState<AuthMode>('login');

  // Login form state
  const [username, setUsername] = useState('salesman_a');
  const [password, setPassword] = useState('sales123');

  // Registration form state
  const [regFullName, setRegFullName] = useState('');
  const [regUsername, setRegUsername] = useState('');
  const [regPassword, setRegPassword] = useState('');
  const [regRole, setRegRole] = useState('salesman');
  const [regPhone, setRegPhone] = useState('');

  // Forgot password form state
  const [forgotUsername, setForgotUsername] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Handle Login Submit
  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);
    setIsSubmitting(true);
    try {
      const data = await loginUser(username, password);
      login(data.access_token, {
        id: 0,
        username: data.username,
        full_name: data.full_name,
        role: data.role,
        is_active: true
      });
    } catch (err: any) {
      setError(err.message || 'Incorrect username or password. Please verify credentials.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle Registration Submit
  const handleRegisterSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);
    if (!regUsername || !regPassword || !regFullName) {
      setError('Please fill in all mandatory fields.');
      return;
    }
    setIsSubmitting(true);
    try {
      const data = await registerUser({
        username: regUsername.trim(),
        password: regPassword,
        full_name: regFullName.trim(),
        role: regRole,
        phone: regPhone.trim() || undefined
      });
      setSuccessMsg(`Account created for ${data.full_name}. Signing into portal...`);
      setTimeout(() => {
        login(data.access_token, {
          id: 0,
          username: data.username,
          full_name: data.full_name,
          role: data.role,
          is_active: true
        });
      }, 800);
    } catch (err: any) {
      setError(err.message || 'Registration failed.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle Forgot Password Submit
  const handleForgotSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);
    if (!forgotUsername || !newPassword) {
      setError('Please provide username and new password.');
      return;
    }
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }
    setIsSubmitting(true);
    try {
      const res = await resetPassword({
        username: forgotUsername.trim(),
        new_password: newPassword
      });
      setSuccessMsg(res.message);
      setUsername(forgotUsername.trim());
      setPassword(newPassword);
      setTimeout(() => {
        setMode('login');
        setSuccessMsg('Password updated. You can now sign in with your new credentials.');
      }, 1200);
    } catch (err: any) {
      setError(err.message || 'Password reset failed.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const quickRoles = [
    { label: 'Salesman A', u: 'salesman_a', p: 'sales123', role: 'Sales / Retail Orders' },
    { label: 'Factory Admin', u: 'admin', p: 'admin123', role: 'Approval & Invoicing' },
    { label: 'Production', u: 'production', p: 'prod123', role: 'BOM & Batch Runs' },
    { label: 'Accountant', u: 'accountant', p: 'acct123', role: 'Read-only Audit' },
    { label: 'Owner', u: 'owner', p: 'owner123', role: 'Executive Overview' },
  ];

  return (
    <div className="min-h-screen graph-paper-grid relative flex flex-col justify-between p-4 sm:p-6 text-soil">
      {/* 1) Twinkling Grid Background Canvas (Fixed, snaps to 32px grid on empty clicks) */}
      <TwinkleCanvas />

      {/* Top Utility Bar on Login Screen */}
      <div className="relative z-20 max-w-5xl w-full mx-auto flex justify-between items-center mb-3">
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-mono text-soil-muted uppercase tracking-wider font-semibold">
            Sri Lakshmi Snacks • Tiruchirappalli
          </span>
        </div>

        {/* Global Controls: Animations & Guides Toggle, Language Toggle, Day/Night Toggle */}
        <div className="flex items-center gap-2 text-xs">
          {/* Settings Toggle: Animations and guides (stored per user) */}
          <button
            type="button"
            onClick={toggleAnimationsAndGuides}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded border transition font-medium ${
              animationsAndGuides
                ? 'solid-card border-terracotta text-terracotta font-semibold'
                : 'solid-card text-soil-muted opacity-80 hover:opacity-100'
            }`}
            title="Toggle interactive grid twinkles and staff guide character"
          >
            <Sparkles className={`w-3.5 h-3.5 ${animationsAndGuides ? 'text-turmeric' : 'text-soil-muted'}`} />
            <span className="hidden sm:inline">
              {language === 'ta' ? 'வழிகாட்டிகள்' : 'Guides & Twinkles'}:
            </span>
            <span className="text-[10px] uppercase font-bold px-1 rounded bg-card-subtle">
              {animationsAndGuides ? (language === 'ta' ? 'ஆன்' : 'ON') : (language === 'ta' ? 'ஆஃப்' : 'OFF')}
            </span>
          </button>

          {/* Language Toggle */}
          <div className="flex items-center solid-card rounded p-0.5 border border-card-border">
            <button
              type="button"
              onClick={() => changeLanguage('en')}
              className={`px-2 py-0.5 rounded text-xs font-semibold transition ${
                language === 'en'
                  ? 'bg-terracotta text-white font-bold'
                  : 'text-soil-muted hover:text-soil'
              }`}
            >
              EN
            </button>
            <button
              type="button"
              onClick={() => changeLanguage('ta')}
              className={`px-2 py-0.5 rounded text-xs font-semibold font-tamil transition ${
                language === 'ta'
                  ? 'bg-terracotta text-white font-bold'
                  : 'text-soil-muted hover:text-soil'
              }`}
            >
              தமிழ்
            </button>
          </div>

          {/* Day / Night Theme Toggle */}
          <button
            type="button"
            onClick={toggleTheme}
            className="flex items-center gap-1 px-2.5 py-1 rounded solid-card border border-card-border text-soil hover:border-terracotta transition font-medium"
            title="Toggle Day/Night mode"
          >
            {theme === 'day' ? (
              <>
                <Sun className="w-3.5 h-3.5 text-turmeric" />
                <span className="hidden md:inline">Day</span>
              </>
            ) : (
              <>
                <Moon className="w-3.5 h-3.5 text-turmeric" />
                <span className="hidden md:inline">Night</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Main 12-Column Grid Container */}
      <div className="relative z-10 w-full max-w-5xl mx-auto solid-card rounded-lg overflow-hidden grid grid-cols-1 lg:grid-cols-12 border border-card-border my-auto shadow-sm">
        
        {/* Left Column (5 of 12 cols): Hand-Crafted South Indian Factory Illustration Hero */}
        <div className="lg:col-span-5 bg-card-subtle p-6 sm:p-8 border-b lg:border-b-0 lg:border-r border-card-border flex flex-col justify-between">
          <div>
            {/* Header Identity Badge */}
            <div className="flex items-center gap-2 mb-3">
              <span className="rubber-stamp rubber-stamp-approved">
                <ShieldCheck className="w-3.5 h-3.5" />
                <span>TN-33 Registered</span>
              </span>
              <span className="text-xs text-soil-muted font-mono">EST. 1988</span>
            </div>

            <h1 className="text-2xl sm:text-3xl font-heading font-bold text-soil leading-tight">
              Sri Lakshmi Snacks
            </h1>
            <p className="font-tamil text-sm text-terracotta font-semibold mt-0.5">
              ஸ்ரீ லக்ஷ்மி ஸ்நாக்ஸ் • திருச்சிராப்பள்ளி
            </p>
            <p className="text-xs text-soil-muted mt-2 leading-relaxed">
              Order-to-Audit Factory ERP • Thuvakudi Industrial Estate, Tiruchirappalli, Tamil Nadu
            </p>

            <KolamDivider className="my-4" />

            {/* Hand-Drawn Village Street & Factory 2D Illustration */}
            <div className="rounded-md border border-card-border overflow-hidden bg-card shadow-xs mt-3">
              <img
                src="/illustrations/factory_village_hero.svg"
                alt="Sri Lakshmi Snacks village factory and traditional shops in Tiruchirappalli"
                loading="lazy"
                className="w-full h-auto object-cover block"
                width="800"
                height="540"
              />
            </div>
          </div>

          {/* Calm Heritage Notes at Base */}
          <div className="mt-6 pt-4 border-t border-card-border text-xs text-soil-muted space-y-1.5">
            <div className="flex items-center justify-between text-[11px] font-mono">
              <span>GSTIN: 33AABCS1234F1Z8</span>
              <span className="font-semibold text-soil">State Code: 33 (TN)</span>
            </div>
            <p className="text-[11px] leading-normal">
              Single append-only stock ledger source of truth. Click empty cream spaces to ripple four-point grid stars.
            </p>
          </div>
        </div>

        {/* Right Column (7 of 12 cols): Structured Authentication & Registration Workspace */}
        <div className="lg:col-span-7 p-6 sm:p-10 flex flex-col justify-between bg-card">
          <div>
            {/* Section Pattern: Small uppercase label + Clear Heading */}
            <div className="mb-4">
              <span className="text-[11px] font-mono font-bold uppercase tracking-wider text-soil-muted block">
                Factory Access Portal
              </span>
              <div className="flex items-center justify-between mt-1">
                <h2 className="text-xl sm:text-2xl font-heading font-bold text-soil">
                  {mode === 'login' && 'Staff Sign In'}
                  {mode === 'register' && 'New Staff Member Registration'}
                  {mode === 'forgot' && 'Reset Staff Password'}
                </h2>
                <span className="text-xs font-tamil text-soil-muted">
                  {mode === 'login' && 'உள்நுழைக'}
                  {mode === 'register' && 'புதிய பதிவு'}
                  {mode === 'forgot' && 'கடவுச்சொல்'}
                </span>
              </div>
            </div>

            {/* Navigational Tabs: Clean Terracotta Underlines */}
            <div className="flex border-b border-card-border mb-6 gap-4 overflow-x-auto">
              <button
                type="button"
                onClick={() => { setMode('login'); setError(null); setSuccessMsg(null); }}
                className={`pb-2.5 text-xs sm:text-sm font-semibold border-b-2 transition flex items-center gap-1.5 whitespace-nowrap ${
                  mode === 'login'
                    ? 'border-terracotta text-terracotta font-bold'
                    : 'border-transparent text-soil-muted hover:text-soil'
                }`}
              >
                <LogIn className="w-4 h-4" />
                <span>Sign In</span>
              </button>
              <button
                type="button"
                onClick={() => { setMode('register'); setError(null); setSuccessMsg(null); }}
                className={`pb-2.5 text-xs sm:text-sm font-semibold border-b-2 transition flex items-center gap-1.5 whitespace-nowrap ${
                  mode === 'register'
                    ? 'border-terracotta text-terracotta font-bold'
                    : 'border-transparent text-soil-muted hover:text-soil'
                }`}
              >
                <UserPlus className="w-4 h-4" />
                <span>New Registration</span>
              </button>
              <button
                type="button"
                onClick={() => { setMode('forgot'); setError(null); setSuccessMsg(null); }}
                className={`pb-2.5 text-xs sm:text-sm font-semibold border-b-2 transition flex items-center gap-1.5 whitespace-nowrap ${
                  mode === 'forgot'
                    ? 'border-terracotta text-terracotta font-bold'
                    : 'border-transparent text-soil-muted hover:text-soil'
                }`}
              >
                <KeyRound className="w-4 h-4" />
                <span>Forgot Password?</span>
              </button>
            </div>

            {/* Notice / Feedback Banners */}
            {error && (
              <div className="mb-4 p-3 bg-chilli/10 border border-chilli text-chilli text-xs rounded flex items-start gap-2">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}
            {successMsg && (
              <div className="mb-4 p-3 bg-leaf/10 border border-leaf text-leaf text-xs rounded flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5" />
                <span>{successMsg}</span>
              </div>
            )}

            {/* ===================== FORM 1: SIGN IN ===================== */}
            {mode === 'login' && (
              <form onSubmit={handleLoginSubmit} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-soil uppercase tracking-wider mb-1.5">
                    Username / பயனர் பெயர்
                  </label>
                  <input
                    id="login-username-input"
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="w-full h-11 px-3.5 bg-card border border-card-border rounded text-soil text-sm focus:outline-none focus:border-terracotta transition"
                    required
                  />
                </div>

                <div>
                  <div className="flex justify-between items-center mb-1.5">
                    <label className="block text-xs font-semibold text-soil uppercase tracking-wider">
                      Password / கடவுச்சொல்
                    </label>
                    <button
                      type="button"
                      onClick={() => { setMode('forgot'); setError(null); }}
                      className="text-xs text-terracotta hover:underline font-medium"
                    >
                      Forgot Password?
                    </button>
                  </div>
                  <input
                    id="login-password-input"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full h-11 px-3.5 bg-card border border-card-border rounded text-soil text-sm focus:outline-none focus:border-terracotta transition"
                    required
                  />
                </div>

                <button
                  id="login-submit-btn"
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full h-12 bg-terracotta hover:bg-terracotta-hover text-white font-bold rounded touch-target transition shadow-xs flex items-center justify-center gap-2 text-sm mt-3"
                >
                  <span>{isSubmitting ? 'Verifying...' : 'Sign In to Portal'}</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </form>
            )}

            {/* ===================== FORM 2: NEW STAFF REGISTRATION ===================== */}
            {mode === 'register' && (
              <form onSubmit={handleRegisterSubmit} className="space-y-3.5">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-semibold text-soil uppercase tracking-wider mb-1">
                      Full Name / முழு பெயர் *
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. K. Murugesan"
                      value={regFullName}
                      onChange={(e) => setRegFullName(e.target.value)}
                      className="w-full h-10 px-3 bg-card border border-card-border rounded text-sm text-soil focus:outline-none focus:border-terracotta"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-soil uppercase tracking-wider mb-1">
                      Username / பயனர் பெயர் *
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. murugesan_sales"
                      value={regUsername}
                      onChange={(e) => setRegUsername(e.target.value)}
                      className="w-full h-10 px-3 bg-card border border-card-border rounded text-sm text-soil focus:outline-none focus:border-terracotta"
                      required
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-semibold text-soil uppercase tracking-wider mb-1">
                      Password (min 4 chars) *
                    </label>
                    <input
                      type="password"
                      value={regPassword}
                      onChange={(e) => setRegPassword(e.target.value)}
                      className="w-full h-10 px-3 bg-card border border-card-border rounded text-sm text-soil focus:outline-none focus:border-terracotta"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-soil uppercase tracking-wider mb-1">
                      Phone Number (optional)
                    </label>
                    <input
                      type="tel"
                      placeholder="+91 94431 23456"
                      value={regPhone}
                      onChange={(e) => setRegPhone(e.target.value)}
                      className="w-full h-10 px-3 bg-card border border-card-border rounded text-sm text-soil focus:outline-none focus:border-terracotta"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-soil uppercase tracking-wider mb-1">
                    Operational Role / பணிப்பொறுப்பு *
                  </label>
                  <select
                    value={regRole}
                    onChange={(e) => setRegRole(e.target.value)}
                    className="w-full h-10 px-3 bg-card border border-card-border rounded text-sm text-soil focus:outline-none focus:border-terracotta"
                  >
                    <option value="salesman">Salesman (Field Orders, Voice Dictation, Stock Check)</option>
                    <option value="production">Production Supervisor (BOM, Batch Execution, Variance)</option>
                    <option value="accountant">Accountant (Read-only Registers, GST Summary, Exports)</option>
                    <option value="admin">Factory Admin (Order Approval, GST Invoices, Dispatch)</option>
                  </select>
                </div>

                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full h-11 bg-leaf hover:bg-leaf-hover text-white font-bold rounded touch-target transition shadow-xs text-sm mt-2 flex items-center justify-center gap-2"
                >
                  <UserPlus className="w-4 h-4" />
                  <span>{isSubmitting ? 'Registering...' : 'Register Staff Member'}</span>
                </button>
              </form>
            )}

            {/* ===================== FORM 3: FORGOT PASSWORD ===================== */}
            {mode === 'forgot' && (
              <form onSubmit={handleForgotSubmit} className="space-y-3.5">
                <p className="text-xs text-soil-muted">
                  Provide your registered staff username to update your password credentials.
                </p>

                <div>
                  <label className="block text-xs font-semibold text-soil uppercase tracking-wider mb-1">
                    Registered Username / பயனர் பெயர் *
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. salesman_a"
                    value={forgotUsername}
                    onChange={(e) => setForgotUsername(e.target.value)}
                    className="w-full h-10 px-3 bg-card border border-card-border rounded text-sm text-soil focus:outline-none focus:border-terracotta"
                    required
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-soil uppercase tracking-wider mb-1">
                    New Password / புதிய கடவுச்சொல் *
                  </label>
                  <input
                    type="password"
                    placeholder="Enter new password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    className="w-full h-10 px-3 bg-card border border-card-border rounded text-sm text-soil focus:outline-none focus:border-terracotta"
                    required
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-soil uppercase tracking-wider mb-1">
                    Confirm New Password / உறுதிப்படுத்துக *
                  </label>
                  <input
                    type="password"
                    placeholder="Re-enter new password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="w-full h-10 px-3 bg-card border border-card-border rounded text-sm text-soil focus:outline-none focus:border-terracotta"
                    required
                  />
                </div>

                <div className="flex gap-2.5 pt-1">
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="flex-1 h-11 bg-terracotta hover:bg-terracotta-hover text-white font-bold rounded touch-target transition shadow-xs text-sm"
                  >
                    {isSubmitting ? 'Updating...' : 'Save New Password'}
                  </button>
                  <button
                    type="button"
                    onClick={() => setMode('login')}
                    className="px-4 h-11 border border-card-border rounded text-xs font-semibold text-soil-muted hover:text-soil hover:bg-card-subtle transition"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            )}
          </div>

          {/* Quick Pre-Seeded Test Roster (Practical for evaluation) */}
          <div id="quick-roster-section" className="mt-8 pt-4 border-t border-card-border">
            <div className="flex justify-between items-center mb-2.5">
              <span className="text-[11px] font-mono font-bold text-soil-muted uppercase tracking-wider">
                Pre-Seeded Roster (Click to Fill)
              </span>
              <span className="text-[10px] font-mono text-soil-muted">
                5 Roles Seeded
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs">
              {quickRoles.map((r) => {
                const isActive = username === r.u && mode === 'login';
                return (
                  <button
                    key={r.u}
                    type="button"
                    onClick={() => {
                      setMode('login');
                      setUsername(r.u);
                      setPassword(r.p);
                    }}
                    className={`p-2.5 rounded border text-left transition flex flex-col justify-between ${
                      isActive
                        ? 'border-terracotta bg-card-subtle font-semibold text-soil'
                        : 'border-card-border bg-card text-soil-muted hover:border-terracotta hover:text-soil'
                    }`}
                  >
                    <span className="font-bold text-[11px] text-soil">{r.label}</span>
                    <span className="text-[10px] text-soil-muted truncate mt-0.5">{r.role}</span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>

      </div>

      {/* 2) Guide Character: Shopkeeper Assistant welcoming staff or pointing to roster/errors */}
      <div className="relative z-30 max-w-5xl w-full mx-auto mt-3">
        {error ? (
          <GuideHelper
            targetSelector="#login-username-input"
            character="shopkeeper"
            screenKey="login_error"
            forceShow={true}
            side="right"
            messageEn="Please verify your staff username and password, or click one of the quick test accounts above to sign in."
            messageTa="தயவுசெய்து உங்கள் பயனர் பெயர் மற்றும் கடவுச்சொல்லை சரிபார்க்கவும் அல்லது மேலே உள்ள மாதிரி கணக்கை கிளிக் செய்யவும்."
          />
        ) : (
          <GuideHelper
            targetSelector="#quick-roster-section"
            character="shopkeeper"
            screenKey="login_welcome"
            idleTimeoutSeconds={6}
            side="left"
            messageEn="Welcome to Sri Lakshmi Snacks! Pick any test account above for instant one-click login, or enter your credentials."
            messageTa="ஸ்ரீ லக்ஷ்மி ஸ்நாக்ஸ்-க்கு நல்வரவு! மாதிரி உள்நுழைவுக்கு மேலே உள்ள கணக்கை கிளிக் செய்யவும் அல்லது உங்கள் விவரங்களை உள்ளிடவும்."
          />
        )}
      </div>
    </div>
  );
};
