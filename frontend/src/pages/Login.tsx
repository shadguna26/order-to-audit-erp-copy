import React, { useState } from 'react';
import { loginUser, registerUser, resetPassword } from '../api/client';
import { useAuth } from '../context/AuthContext';

type AuthMode = 'login' | 'register' | 'forgot';

export const Login: React.FC = () => {
  const { login } = useAuth();
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
      setError(err.message || 'Login failed. Please check credentials.');
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
      setSuccessMsg(`Account created for ${data.full_name}! Signing you in...`);
      setTimeout(() => {
        login(data.access_token, {
          id: 0,
          username: data.username,
          full_name: data.full_name,
          role: data.role,
          is_active: true
        });
      }, 900);
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
        setSuccessMsg('Password updated! You can now sign in with your new password.');
      }, 1200);
    } catch (err: any) {
      setError(err.message || 'Password reset failed.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const quickRoles = [
    { label: 'Salesman A', u: 'salesman_a', p: 'sales123', role: 'Sales / Retail Orders' },
    { label: 'Factory Admin', u: 'admin', p: 'admin123', role: 'Orders, Invoicing & Dispatch' },
    { label: 'Production', u: 'production', p: 'prod123', role: 'BOM & Batch Runs' },
    { label: 'Accountant', u: 'accountant', p: 'acct123', role: 'Audit Registers & GST' },
    { label: 'Owner', u: 'owner', p: 'owner123', role: 'Executive Overview' },
  ];

  return (
    <div className="min-h-screen bg-cream dark:bg-stone-950 flex items-center justify-center p-3 sm:p-6 text-stone-900 dark:text-stone-100">
      <div className="w-full max-w-5xl bg-white dark:bg-stone-900 border border-stone-300 dark:border-stone-800 rounded-xl shadow-xl overflow-hidden grid grid-cols-1 lg:grid-cols-12 min-h-[640px]">
        
        {/* Left Column: Authentic South Indian Market Heritage Hero */}
        <div className="lg:col-span-5 relative bg-stone-900 flex flex-col justify-between p-6 sm:p-8 text-white overflow-hidden min-h-[300px] lg:min-h-auto">
          {/* Market Hero Image with gradient overlay */}
          <div className="absolute inset-0 z-0">
            <img
              src="/images/market_hero.jpg"
              alt="Sri Lakshmi Snacks Traditional Market Bazaar"
              className="w-full h-full object-cover object-center opacity-75 transform scale-105 hover:scale-100 transition-transform duration-1000"
              onError={(e) => {
                // Fallback to png if jpg fails
                (e.target as HTMLImageElement).src = '/images/market_hero.png';
              }}
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black/95 via-black/60 to-black/30" />
          </div>

          {/* Header Brand Badge */}
          <div className="relative z-10 space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-turmeric-600/90 border border-turmeric-400 text-white text-[11px] font-bold uppercase tracking-wider rounded-full shadow-sm">
              <span>🌾</span>
              <span>Traditional South Indian Snack House</span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white leading-tight">
              ஸ்ரீ லக்ஷ்மி ஸ்நாக்ஸ்
            </h2>
            <p className="text-xs text-amber-200 font-medium">
              Sri Lakshmi Snacks • Thuvakudi Industrial Estate, Tiruchirappalli
            </p>
          </div>

          {/* Center Showcase Details */}
          <div className="relative z-10 my-6 space-y-3">
            <div className="bg-black/50 backdrop-blur-xs border border-white/10 rounded-lg p-3 text-xs space-y-1.5">
              <div className="flex items-center gap-2 text-amber-300 font-bold">
                <span>✨</span>
                <span>Authentic Taste • Pure Sesame & Groundnut Oil</span>
              </div>
              <p className="text-[11px] text-stone-300 leading-relaxed">
                Handcrafted Kai Murukku, spicy Madras Mixture, Ribbon Pakoda, Thattai and ghee sweets prepared daily according to legacy Tamil recipes.
              </p>
            </div>

            <div className="grid grid-cols-2 gap-2 text-[11px]">
              <div className="bg-white/10 border border-white/10 rounded p-2 text-center">
                <span className="block font-bold text-white text-base">33AABCS...</span>
                <span className="text-stone-300 text-[10px]">TN GST Registered</span>
              </div>
              <div className="bg-white/10 border border-white/10 rounded p-2 text-center">
                <span className="block font-bold text-turmeric-400 text-base">100% Audit</span>
                <span className="text-stone-300 text-[10px]">Append-Only Ledger</span>
              </div>
            </div>
          </div>

          {/* Bottom Footer Quote */}
          <div className="relative z-10 border-t border-white/20 pt-3 flex justify-between items-center text-[11px] text-stone-300">
            <span>Tiruchirappalli, Tamil Nadu</span>
            <span className="font-mono text-amber-300">EST. 1988</span>
          </div>
        </div>

        {/* Right Column: Authentication & Staff Registration Hub */}
        <div className="lg:col-span-7 p-6 sm:p-10 flex flex-col justify-between bg-white dark:bg-stone-900">
          <div>
            {/* Top Navigation Tabs: Sign In / Register / Forgot Password */}
            <div className="flex border-b border-stone-200 dark:border-stone-800 pb-3 mb-6 gap-2 sm:gap-4 overflow-x-auto">
              <button
                type="button"
                onClick={() => { setMode('login'); setError(null); setSuccessMsg(null); }}
                className={`pb-2 text-xs sm:text-sm font-bold border-b-2 transition whitespace-nowrap ${
                  mode === 'login'
                    ? 'border-turmeric-600 text-turmeric-700 dark:text-turmeric-400'
                    : 'border-transparent text-stone-500 hover:text-stone-900 dark:hover:text-stone-300'
                }`}
              >
                Sign In (உள்நுழைக)
              </button>
              <button
                type="button"
                onClick={() => { setMode('register'); setError(null); setSuccessMsg(null); }}
                className={`pb-2 text-xs sm:text-sm font-bold border-b-2 transition whitespace-nowrap ${
                  mode === 'register'
                    ? 'border-turmeric-600 text-turmeric-700 dark:text-turmeric-400'
                    : 'border-transparent text-stone-500 hover:text-stone-900 dark:hover:text-stone-300'
                }`}
              >
                New Staff Registration (பதிவு)
              </button>
              <button
                type="button"
                onClick={() => { setMode('forgot'); setError(null); setSuccessMsg(null); }}
                className={`pb-2 text-xs sm:text-sm font-bold border-b-2 transition whitespace-nowrap ${
                  mode === 'forgot'
                    ? 'border-turmeric-600 text-turmeric-700 dark:text-turmeric-400'
                    : 'border-transparent text-stone-500 hover:text-stone-900 dark:hover:text-stone-300'
                }`}
              >
                Forgot Password?
              </button>
            </div>

            {/* Error & Success Banners */}
            {error && (
              <div className="mb-4 p-3 bg-rose-50 dark:bg-rose-950/40 border border-rose-300 dark:border-rose-800 text-rose-700 dark:text-rose-300 text-xs rounded-md">
                {error}
              </div>
            )}
            {successMsg && (
              <div className="mb-4 p-3 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-300 dark:border-emerald-800 text-emerald-700 dark:text-emerald-300 text-xs rounded-md">
                {successMsg}
              </div>
            )}

            {/* ===================== TAB 1: SIGN IN ===================== */}
            {mode === 'login' && (
              <form onSubmit={handleLoginSubmit} className="space-y-4">
                <div>
                  <label className="block text-xs font-bold text-stone-700 dark:text-stone-300 uppercase tracking-wide mb-1">
                    Staff Username (பயனர் பெயர்)
                  </label>
                  <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="w-full h-11 px-3 border border-stone-300 dark:border-stone-700 rounded-md bg-stone-50 dark:bg-stone-800 text-stone-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-turmeric-600 text-sm"
                    required
                  />
                </div>

                <div>
                  <div className="flex justify-between items-center mb-1">
                    <label className="block text-xs font-bold text-stone-700 dark:text-stone-300 uppercase tracking-wide">
                      Password (கடவுச்சொல்)
                    </label>
                    <button
                      type="button"
                      onClick={() => { setMode('forgot'); setError(null); }}
                      className="text-[11px] text-turmeric-700 dark:text-turmeric-400 hover:underline font-semibold"
                    >
                      Forgot?
                    </button>
                  </div>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full h-11 px-3 border border-stone-300 dark:border-stone-700 rounded-md bg-stone-50 dark:bg-stone-800 text-stone-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-turmeric-600 text-sm"
                    required
                  />
                </div>

                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full h-12 bg-turmeric-600 hover:bg-turmeric-700 text-white font-bold rounded-md touch-target transition shadow-md text-sm mt-2"
                >
                  {isSubmitting ? 'Verifying Credentials...' : 'Sign In to Portal'}
                </button>
              </form>
            )}

            {/* ===================== TAB 2: NEW STAFF REGISTRATION ===================== */}
            {mode === 'register' && (
              <form onSubmit={handleRegisterSubmit} className="space-y-3.5">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-bold text-stone-700 dark:text-stone-300 uppercase mb-1">
                      Full Name (முழு பெயர்) *
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. K. Murugesan"
                      value={regFullName}
                      onChange={(e) => setRegFullName(e.target.value)}
                      className="w-full h-10 px-3 border border-stone-300 dark:border-stone-700 rounded bg-stone-50 dark:bg-stone-800 text-sm text-stone-900 dark:text-white"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-stone-700 dark:text-stone-300 uppercase mb-1">
                      Username (பயனர் பெயர்) *
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. murugesan_sales"
                      value={regUsername}
                      onChange={(e) => setRegUsername(e.target.value)}
                      className="w-full h-10 px-3 border border-stone-300 dark:border-stone-700 rounded bg-stone-50 dark:bg-stone-800 text-sm text-stone-900 dark:text-white"
                      required
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-bold text-stone-700 dark:text-stone-300 uppercase mb-1">
                      Password (கடவுச்சொல்) *
                    </label>
                    <input
                      type="password"
                      placeholder="Min 4 characters"
                      value={regPassword}
                      onChange={(e) => setRegPassword(e.target.value)}
                      className="w-full h-10 px-3 border border-stone-300 dark:border-stone-700 rounded bg-stone-50 dark:bg-stone-800 text-sm text-stone-900 dark:text-white"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-stone-700 dark:text-stone-300 uppercase mb-1">
                      Phone Number (தொலைபேசி)
                    </label>
                    <input
                      type="tel"
                      placeholder="+91 98765 43210"
                      value={regPhone}
                      onChange={(e) => setRegPhone(e.target.value)}
                      className="w-full h-10 px-3 border border-stone-300 dark:border-stone-700 rounded bg-stone-50 dark:bg-stone-800 text-sm text-stone-900 dark:text-white"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-stone-700 dark:text-stone-300 uppercase mb-1">
                    Assign Staff Operational Role (பணிப்பொறுப்பு) *
                  </label>
                  <select
                    value={regRole}
                    onChange={(e) => setRegRole(e.target.value)}
                    className="w-full h-10 px-3 border border-stone-300 dark:border-stone-700 rounded bg-stone-50 dark:bg-stone-800 text-sm text-stone-900 dark:text-white"
                  >
                    <option value="salesman">Salesman (Order Entry, Voice Input, Shortage Warning)</option>
                    <option value="production">Production Supervisor (BOM, Batch Execution, Variance)</option>
                    <option value="accountant">Accountant (Read-only Audit Registers, GST Summary)</option>
                    <option value="admin">Factory Admin (Order Approval, GST Invoices, Dispatch)</option>
                  </select>
                </div>

                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full h-11 bg-leaf-600 hover:bg-leaf-700 text-white font-bold rounded touch-target transition shadow-sm text-sm"
                >
                  {isSubmitting ? 'Registering...' : 'Register New Staff Member'}
                </button>
              </form>
            )}

            {/* ===================== TAB 3: FORGOT PASSWORD ===================== */}
            {mode === 'forgot' && (
              <form onSubmit={handleForgotSubmit} className="space-y-4">
                <p className="text-xs text-stone-500">
                  Enter your registered staff username to set a new password.
                </p>

                <div>
                  <label className="block text-xs font-bold text-stone-700 dark:text-stone-300 uppercase mb-1">
                    Registered Username (பயனர் பெயர்) *
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. salesman_a"
                    value={forgotUsername}
                    onChange={(e) => setForgotUsername(e.target.value)}
                    className="w-full h-11 px-3 border border-stone-300 dark:border-stone-700 rounded bg-stone-50 dark:bg-stone-800 text-sm text-stone-900 dark:text-white"
                    required
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-stone-700 dark:text-stone-300 uppercase mb-1">
                    New Password (புதிய கடவுச்சொல்) *
                  </label>
                  <input
                    type="password"
                    placeholder="Enter new password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    className="w-full h-11 px-3 border border-stone-300 dark:border-stone-700 rounded bg-stone-50 dark:bg-stone-800 text-sm text-stone-900 dark:text-white"
                    required
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-stone-700 dark:text-stone-300 uppercase mb-1">
                    Confirm New Password (கடவுச்சொல் உறுதி) *
                  </label>
                  <input
                    type="password"
                    placeholder="Re-type new password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="w-full h-11 px-3 border border-stone-300 dark:border-stone-700 rounded bg-stone-50 dark:bg-stone-800 text-sm text-stone-900 dark:text-white"
                    required
                  />
                </div>

                <div className="flex gap-2">
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="flex-1 h-11 bg-turmeric-600 hover:bg-turmeric-700 text-white font-bold rounded touch-target transition shadow-sm text-sm"
                  >
                    {isSubmitting ? 'Updating...' : 'Reset Password'}
                  </button>
                  <button
                    type="button"
                    onClick={() => setMode('login')}
                    className="px-4 h-11 border border-stone-300 dark:border-stone-700 rounded text-xs font-semibold hover:bg-stone-100 dark:hover:bg-stone-800"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            )}
          </div>

          {/* Quick Pre-Seeded Accounts Selector (Convenient for Review) */}
          <div className="mt-6 pt-4 border-t border-stone-200 dark:border-stone-800">
            <div className="flex justify-between items-center mb-2">
              <span className="text-[11px] font-bold text-stone-500 uppercase tracking-wider">
                Quick Test Accounts (Click to Fill)
              </span>
              <span className="text-[10px] text-amber-700 dark:text-amber-400 font-mono font-semibold">
                Pre-Seeded Roster
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-1.5 text-xs">
              {quickRoles.map((r) => (
                <button
                  key={r.u}
                  type="button"
                  onClick={() => {
                    setMode('login');
                    setUsername(r.u);
                    setPassword(r.p);
                  }}
                  className={`text-left px-2.5 py-1.5 rounded border transition flex flex-col justify-between ${
                    username === r.u && mode === 'login'
                      ? 'border-turmeric-600 bg-amber-50/70 dark:bg-amber-950/40 text-stone-900 dark:text-white'
                      : 'border-stone-200 dark:border-stone-800 hover:border-turmeric-500 bg-white dark:bg-stone-800 text-stone-700 dark:text-stone-300'
                  }`}
                >
                  <span className="font-bold text-[11px]">{r.label}</span>
                  <span className="text-[10px] text-stone-500 truncate">{r.role}</span>
                </button>
              ))}
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};
