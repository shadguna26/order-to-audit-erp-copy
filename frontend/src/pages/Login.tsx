import React, { useState } from 'react';
import { loginUser } from '../api/client';
import { useAuth } from '../context/AuthContext';

export const Login: React.FC = () => {
  const { login } = useAuth();
  const [username, setUsername] = useState('salesman_a');
  const [password, setPassword] = useState('sales123');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
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
      setError(err.message || 'Login failed');
    } finally {
      setIsSubmitting(false);
    }
  };

  const quickRoles = [
    { label: 'Salesman A', u: 'salesman_a', p: 'sales123', role: 'Sales / Ordering' },
    { label: 'Factory Admin', u: 'admin', p: 'admin123', role: 'Approval & Invoicing' },
    { label: 'Production', u: 'production', p: 'prod123', role: 'BOM & Batches' },
    { label: 'Accountant', u: 'accountant', p: 'acct123', role: 'Read-only Audit' },
    { label: 'Owner', u: 'owner', p: 'owner123', role: 'Executive Overview' },
  ];

  return (
    <div className="min-h-screen flex flex-col justify-center items-center px-4 py-8 bg-cream">
      <div className="w-full max-w-md bg-white border border-stone-300 rounded p-6 shadow-sm">
        <div className="border-b border-stone-200 pb-4 mb-5 text-center">
          <div className="inline-block px-2 py-0.5 text-xs font-semibold uppercase tracking-wider bg-turmeric-100 text-turmeric-700 rounded mb-1">
            Order-to-Audit System
          </div>
          <h1 className="text-xl font-bold text-stone-900">Sri Lakshmi Snacks</h1>
          <p className="text-xs text-stone-600">Thuvakudi Industrial Estate, Tiruchirappalli, Tamil Nadu</p>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-chilli-50 border border-chilli-600/30 text-chilli-700 text-sm rounded">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-stone-700 uppercase tracking-wide mb-1">
              Username
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full h-11 px-3 border border-stone-300 rounded text-stone-900 focus:outline-none focus:border-turmeric-600"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-stone-700 uppercase tracking-wide mb-1">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full h-11 px-3 border border-stone-300 rounded text-stone-900 focus:outline-none focus:border-turmeric-600"
              required
            />
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full h-12 bg-turmeric-600 hover:bg-turmeric-700 text-white font-medium rounded touch-target transition-colors shadow-sm"
          >
            {isSubmitting ? 'Verifying...' : 'Sign In'}
          </button>
        </form>

        <div className="mt-6 pt-5 border-t border-stone-200">
          <span className="block text-xs font-semibold text-stone-500 uppercase tracking-wider mb-2">
            Quick Test Accounts (Phase 1)
          </span>
          <div className="grid grid-cols-1 gap-1.5 text-xs">
            {quickRoles.map((r) => (
              <button
                key={r.u}
                type="button"
                onClick={() => {
                  setUsername(r.u);
                  setPassword(r.p);
                }}
                className={`text-left px-3 py-2 rounded border border-stone-200 hover:border-turmeric-500 hover:bg-cream-100 transition flex justify-between items-center ${
                  username === r.u ? 'border-turmeric-600 bg-amber-50/50' : 'bg-white'
                }`}
              >
                <div>
                  <span className="font-semibold text-stone-900">{r.label}</span>
                  <span className="text-stone-500 ml-2">({r.u})</span>
                </div>
                <span className="text-stone-500 text-[11px]">{r.role}</span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
