import React, { useState, useEffect } from 'react';
import { useAuth } from './context/AuthContext';
import { useTheme } from './context/ThemeContext';
import { useTranslation } from 'react-i18next';
import { Login } from './pages/Login';
import { SalesmanScreen } from './pages/SalesmanScreen';
import { AdminScreen } from './pages/AdminScreen';
import { ProductionScreen } from './pages/ProductionScreen';
import { AccountantScreen } from './pages/AccountantScreen';
import { OwnerScreen } from './pages/OwnerScreen';
import { StockLedgerModal } from './components/StockLedgerModal';

type TabKey = 'salesman' | 'admin' | 'production' | 'accountant' | 'owner';

export const App: React.FC = () => {
  const { user, token, logout, isLoading } = useAuth();
  const { theme, toggleTheme, language, changeLanguage } = useTheme();
  const { t } = useTranslation();

  const [activeTab, setActiveTab] = useState<TabKey>('salesman');
  const [stockModal, setStockModal] = useState<{ isOpen: boolean; itemType: string; itemId: number }>({
    isOpen: false,
    itemType: 'finished_goods',
    itemId: 1
  });

  // Set default tab on login based on user role
  useEffect(() => {
    if (user?.role) {
      if (user.role === 'salesman') setActiveTab('salesman');
      else if (user.role === 'production') setActiveTab('production');
      else if (user.role === 'accountant') setActiveTab('accountant');
      else if (user.role === 'admin') setActiveTab('admin');
      else if (user.role === 'owner') setActiveTab('owner');
    }
  }, [user?.role]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-cream text-stone-600 text-sm">
        Loading system session...
      </div>
    );
  }

  if (!user || !token) {
    return <Login />;
  }

  const handleOpenStockLedger = (itemType: string, itemId: number) => {
    setStockModal({
      isOpen: true,
      itemType,
      itemId
    });
  };

  // Determine authorized tabs based on user role
  const isSuperUser = user.role === 'admin' || user.role === 'owner';
  const availableTabs: { key: TabKey; label: string; roleFilter: string[] }[] = [
    { key: 'salesman', label: language === 'ta' ? 'விற்பனை ஆர்டர்' : 'Salesman Order', roleFilter: ['salesman', 'admin', 'owner'] },
    { key: 'admin', label: language === 'ta' ? 'தொழிற்சாலை நிர்வாகம்' : 'Factory Admin', roleFilter: ['admin', 'owner'] },
    { key: 'production', label: language === 'ta' ? 'தயாரிப்பு & திட்டம்' : 'Production & BOM', roleFilter: ['production', 'admin', 'owner'] },
    { key: 'accountant', label: language === 'ta' ? 'தணிக்கை & பதிவேடுகள்' : 'Accountant Registers', roleFilter: ['accountant', 'admin', 'owner'] },
    { key: 'owner', label: language === 'ta' ? 'உரிமையாளர் முகப்பு' : 'Owner Dashboard', roleFilter: ['owner', 'admin'] }
  ];

  const visibleTabs = availableTabs.filter(tab => isSuperUser || tab.roleFilter.includes(user.role));

  return (
    <div className="min-h-screen flex flex-col bg-cream dark:bg-stone-950 text-stone-900 dark:text-stone-100 transition-colors">
      {/* Top Application Header */}
      <header className="bg-white dark:bg-stone-900 border-b border-stone-300 dark:border-stone-800 px-4 sm:px-6 py-3 flex flex-wrap justify-between items-center gap-3 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded bg-turmeric-600 flex items-center justify-center text-white font-bold text-lg shadow-sm">
            SL
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs uppercase font-bold text-turmeric-700 dark:text-turmeric-400 tracking-wider">
                {t('brand')} • Tiruchirappalli
              </span>
              <span className="text-[10px] bg-stone-100 dark:bg-stone-800 text-stone-600 dark:text-stone-300 font-mono px-1.5 py-0.5 rounded border border-stone-300 dark:border-stone-700">
                TN-33
              </span>
            </div>
            <h1 className="text-base sm:text-lg font-bold text-stone-900 dark:text-white leading-tight">
              Order-to-Audit ERP
            </h1>
          </div>
        </div>

        {/* Global Controls & User Info */}
        <div className="flex items-center gap-3 sm:gap-4 text-xs">
          {/* Language Toggle */}
          <div className="flex items-center bg-stone-100 dark:bg-stone-800 rounded p-0.5 border border-stone-300 dark:border-stone-700">
            <button
              type="button"
              onClick={() => changeLanguage('en')}
              className={`px-2.5 py-1 rounded font-medium transition ${
                language === 'en'
                  ? 'bg-white dark:bg-stone-700 text-stone-900 dark:text-white shadow-xs font-bold'
                  : 'text-stone-600 dark:text-stone-400 hover:text-stone-900'
              }`}
            >
              EN
            </button>
            <button
              type="button"
              onClick={() => changeLanguage('ta')}
              className={`px-2.5 py-1 rounded font-medium transition ${
                language === 'ta'
                  ? 'bg-white dark:bg-stone-700 text-stone-900 dark:text-white shadow-xs font-bold'
                  : 'text-stone-600 dark:text-stone-400 hover:text-stone-900'
              }`}
            >
              தமிழ்
            </button>
          </div>

          {/* Day / Night Theme Toggle */}
          <button
            type="button"
            onClick={toggleTheme}
            className="flex items-center gap-1.5 px-3 py-1.5 border border-stone-300 dark:border-stone-700 rounded bg-white dark:bg-stone-800 text-stone-700 dark:text-stone-200 hover:bg-stone-50 dark:hover:bg-stone-750 transition font-medium"
            title="Toggle Day/Night mode"
          >
            {theme === 'day' ? (
              <>
                <span>☀️</span>
                <span className="hidden sm:inline">Day Mode</span>
              </>
            ) : (
              <>
                <span>🌙</span>
                <span className="hidden sm:inline">Night Mode</span>
              </>
            )}
          </button>

          {/* User profile & Role Badge */}
          <div className="text-right pl-2 border-l border-stone-300 dark:border-stone-700">
            <div className="font-semibold text-stone-900 dark:text-white">{user.full_name}</div>
            <div className="text-[11px] font-mono uppercase text-stone-500">
              Role: <span className="font-bold text-turmeric-700 dark:text-turmeric-400">{user.role}</span>
            </div>
          </div>

          {/* Sign Out Button */}
          <button
            type="button"
            onClick={logout}
            className="px-3 py-1.5 text-xs border border-stone-300 dark:border-stone-700 hover:border-chilli-600 hover:text-chilli-600 dark:hover:text-chilli-400 rounded bg-white dark:bg-stone-800 text-stone-700 dark:text-stone-300 transition-colors font-medium"
          >
            {t('nav.sign_out')}
          </button>
        </div>
      </header>

      {/* Role Navigation Bar */}
      <nav className="bg-stone-100 dark:bg-stone-900/80 border-b border-stone-300 dark:border-stone-800 px-4 sm:px-6 py-1.5">
        <div className="max-w-7xl mx-auto flex items-center gap-2 overflow-x-auto">
          {visibleTabs.map((tab) => {
            const isActive = activeTab === tab.key;
            return (
              <button
                key={tab.key}
                type="button"
                onClick={() => setActiveTab(tab.key)}
                className={`px-4 py-2 text-xs font-bold rounded transition whitespace-nowrap ${
                  isActive
                    ? 'bg-turmeric-600 text-white shadow-xs'
                    : 'text-stone-600 dark:text-stone-400 hover:bg-stone-200 dark:hover:bg-stone-800'
                }`}
              >
                {tab.label}
              </button>
            );
          })}
        </div>
      </nav>

      {/* Main Screen Content */}
      <main className="flex-1 p-4 sm:p-6 max-w-7xl w-full mx-auto">
        {activeTab === 'salesman' && (
          <SalesmanScreen token={token} user={user} onSelectStock={handleOpenStockLedger} />
        )}
        {activeTab === 'admin' && (
          <AdminScreen token={token} user={user} onSelectStock={handleOpenStockLedger} />
        )}
        {activeTab === 'production' && (
          <ProductionScreen token={token} user={user} onSelectStock={handleOpenStockLedger} />
        )}
        {activeTab === 'accountant' && (
          <AccountantScreen token={token} user={user} onSelectStock={handleOpenStockLedger} />
        )}
        {activeTab === 'owner' && (
          <OwnerScreen token={token} user={user} onSelectStock={handleOpenStockLedger} />
        )}
      </main>

      {/* Drill-down Stock Ledger Modal */}
      <StockLedgerModal
        isOpen={stockModal.isOpen}
        onClose={() => setStockModal((prev) => ({ ...prev, isOpen: false }))}
        itemType={stockModal.itemType}
        itemId={stockModal.itemId}
        token={token}
      />
    </div>
  );
};
