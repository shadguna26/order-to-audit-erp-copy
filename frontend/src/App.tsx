import React from 'react';
import { useAuth } from './context/AuthContext';
import { Login } from './pages/Login';

export const App: React.FC = () => {
  const { user, logout, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-cream text-stone-600 text-sm">
        Loading system session...
      </div>
    );
  }

  if (!user) {
    return <Login />;
  }

  return (
    <div className="min-h-screen flex flex-col bg-cream text-stone-900">
      {/* Top Application Bar */}
      <header className="bg-white border-b border-stone-300 px-6 py-3 flex justify-between items-center">
        <div>
          <span className="text-xs uppercase font-bold text-turmeric-700 tracking-wider">
            Sri Lakshmi Snacks • Tiruchirappalli
          </span>
          <h1 className="text-lg font-bold text-stone-900 leading-tight">
            Order-to-Audit ERP
          </h1>
        </div>
        <div className="flex items-center gap-4 text-sm">
          <div className="text-right">
            <div className="font-medium text-stone-900">{user.full_name}</div>
            <div className="text-xs font-mono uppercase text-stone-500">
              Role: <span className="font-bold text-turmeric-700">{user.role}</span>
            </div>
          </div>
          <button
            onClick={logout}
            className="px-3 py-1.5 text-xs border border-stone-300 hover:border-chilli-600 hover:text-chilli-600 rounded bg-white transition-colors"
          >
            Sign Out
          </button>
        </div>
      </header>

      {/* Main Workspace */}
      <main className="flex-1 p-6 max-w-7xl w-full mx-auto">
        <div className="bg-white border border-stone-300 rounded p-6 shadow-sm">
          <div className="flex items-center justify-between border-b border-stone-200 pb-4 mb-4">
            <div>
              <h2 className="text-base font-bold text-stone-900">Phase 1 Initialized Successfully</h2>
              <p className="text-xs text-stone-600">
                Database schema, append-only stock ledger, and RBAC authentication are verified and ready.
              </p>
            </div>
            <span className="px-2.5 py-1 text-xs font-semibold bg-leaf-50 text-leaf-700 border border-leaf-700/20 rounded">
              Phase 1: Ready for Review
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
            <div className="p-4 border border-stone-200 rounded bg-cream-50">
              <span className="font-semibold text-stone-700 block mb-1">Company Details</span>
              <p className="text-stone-900">Sri Lakshmi Snacks</p>
              <p className="text-stone-600">Tiruchirappalli, Tamil Nadu (State Code 33)</p>
              <p className="text-stone-500 font-mono mt-1">GSTIN: 33AABCS1234F1Z8</p>
            </div>

            <div className="p-4 border border-stone-200 rounded bg-cream-50">
              <span className="font-semibold text-stone-700 block mb-1">Active User Role</span>
              <p className="text-stone-900 font-medium">{user.full_name}</p>
              <p className="text-stone-600 font-mono">Role: {user.role}</p>
              <p className="text-stone-500 mt-1">Status: Authenticated via JWT</p>
            </div>

            <div className="p-4 border border-stone-200 rounded bg-cream-50">
              <span className="font-semibold text-stone-700 block mb-1">Stock Ledger Engine</span>
              <p className="text-stone-900 font-medium">Append-Only Active</p>
              <p className="text-stone-600">Opening balances seeded in base units (g, ml, piece)</p>
              <p className="text-stone-500 mt-1">Next: Phase 2 Ledger & Purchases</p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};
