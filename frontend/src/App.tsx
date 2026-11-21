import React, { useState, useEffect } from 'react';
import { Sun, Moon, LogOut, Building2 } from 'lucide-react';
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
      <div className="min-h-screen flex items-center justify-center bg-page text-soil-muted text-sm font-body">
        Loading session...
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
    <div className="min-h-screen flex flex-col bg-page graph-paper-grid text-soil transition-colors font-body">
      {/* Terracotta Top Application Header */}
      <header className="bg-terracotta text-white px-4 sm:px-6 py-2.5 flex flex-wrap justify-between items-center gap-3 shadow-xs">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded bg-white/10 border border-white/20 flex items-center justify-center text-white shrink-0">
            <Building2 className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[11px] uppercase font-bold tracking-wider text-amber-200">
                {t('brand')} • Tiruchirappalli
              </span>
              <span className="text-[10px] bg-black/20 text-white font-mono px-1.5 py-0.2 rounded border border-white/20">
                TN-33
              </span>
            </div>
            <h1 className="text-base sm:text-lg font-heading font-bold text-white leading-tight">
              Order-to-Audit ERP
            </h1>
          </div>
        </div>

        {/* Global Controls & User Info */}
        <div className="flex items-center gap-3 text-xs">
          {/* Language Toggle */}
          <div className="flex items-center bg-black/20 rounded p-0.5 border border-white/20">
            <button
              type="button"
              onClick={() => changeLanguage('en')}
              className={`px-2 py-0.5 rounded text-xs font-semibold transition ${
                language === 'en'
                  ? 'bg-white text-terracotta font-bold'
                  : 'text-white/80 hover:text-white'
              }`}
            >
              EN
            </button>
            <button
              type="button"
              onClick={() => changeLanguage('ta')}
              className={`px-2 py-0.5 rounded text-xs font-semibold font-tamil transition ${
                language === 'ta'
                  ? 'bg-white text-terracotta font-bold'
                  : 'text-white/80 hover:text-white'
              }`}
            >
              தமிழ்
            </button>
          </div>

          {/* Day / Night Theme Toggle */}
          <button
            type="button"
            onClick={toggleTheme}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-black/20 border border-white/20 text-white hover:bg-black/30 transition text-xs font-medium"
            title="Toggle Day/Night mode"
          >
            {theme === 'day' ? (
              <>
                <Sun className="w-3.5 h-3.5 text-amber-200" />
                <span className="hidden sm:inline">Day</span>
              </>
            ) : (
              <>
                <Moon className="w-3.5 h-3.5 text-amber-200" />
                <span className="hidden sm:inline">Night</span>
              </>
            )}
          </button>

          {/* User profile & Role Badge */}
          <div className="text-right pl-2 border-l border-white/20 hidden sm:block">
            <div className="font-semibold text-white">{user.full_name}</div>
            <div className="text-[10px] font-mono uppercase text-amber-200">
              Role: <span className="font-bold">{user.role}</span>
            </div>
          </div>

          {/* Sign Out Button */}
          <button
            type="button"
            onClick={logout}
            className="flex items-center gap-1 px-2.5 py-1 text-xs border border-white/30 hover:bg-white hover:text-terracotta rounded text-white transition-colors font-semibold"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">{t('nav.sign_out')}</span>
          </button>
        </div>
      </header>

      {/* Role Navigation Bar */}
      <nav className="bg-card solid-card border-x-0 border-t-0 px-4 sm:px-6 py-1.5">
        <div className="max-w-7xl mx-auto flex items-center gap-2 overflow-x-auto">
          {visibleTabs.map((tab) => {
            const isActive = activeTab === tab.key;
            return (
              <button
                key={tab.key}
                type="button"
                onClick={() => setActiveTab(tab.key)}
                className={`px-3.5 py-1.5 text-xs font-bold rounded transition whitespace-nowrap ${
                  isActive
                    ? 'bg-terracotta text-white shadow-xs'
                    : 'text-soil-muted hover:text-soil hover:bg-card-subtle'
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
