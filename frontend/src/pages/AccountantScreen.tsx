import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';

export const AccountantScreen: React.FC<{ token: string; user: any; onSelectStock: (type: string, id: number) => void }> = ({ token, user, onSelectStock }) => {
  const { t } = useTranslation();
  const [salesData, setSalesData] = useState<any[]>([]);
  const [gstData, setGstData] = useState<any | null>(null);
  const [ageingData, setAgeingData] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<'sales' | 'gst' | 'ageing'>('sales');

  useEffect(() => {
    loadReports();
  }, []);

  const loadReports = async () => {
    try {
      const sRes = await fetch('/api/v1/reports/sales-register', { headers: { Authorization: `Bearer ${token}` } });
      if (sRes.ok) setSalesData(await sRes.json());

      const gRes = await fetch('/api/v1/reports/gst-summary', { headers: { Authorization: `Bearer ${token}` } });
      if (gRes.ok) setGstData(await gRes.json());

      const aRes = await fetch('/api/v1/reports/ageing-report', { headers: { Authorization: `Bearer ${token}` } });
      if (aRes.ok) setAgeingData(await aRes.json());
    } catch {}
  };

  return (
    <div className="space-y-5">
      <div className="flex justify-between items-center bg-white dark:bg-stone-900 border border-stone-300 dark:border-stone-700 p-4 rounded">
        <div>
          <h2 className="text-base font-bold text-stone-900 dark:text-white">{t('accountant.title')}</h2>
          <p className="text-xs text-stone-500">Read-only audit registers with CSV and Excel export.</p>
        </div>
        <div className="flex gap-2">
          <a
            href={`/api/v1/reports/${activeTab === 'sales' ? 'sales-register' : activeTab === 'ageing' ? 'ageing-report' : 'purchase-register'}?format=csv`}
            className="px-3 py-1.5 border border-stone-300 font-semibold text-xs rounded bg-white hover:bg-stone-50"
          >
            {t('accountant.export_csv')}
          </a>
          <a
            href={`/api/v1/reports/${activeTab === 'sales' ? 'sales-register' : activeTab === 'ageing' ? 'ageing-report' : 'purchase-register'}?format=excel`}
            className="px-3 py-1.5 bg-leaf-600 hover:bg-leaf-700 text-white font-semibold text-xs rounded"
          >
            {t('accountant.export_excel')}
          </a>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-stone-200">
        <button
          onClick={() => setActiveTab('sales')}
          className={`pb-2 px-3 text-xs font-bold border-b-2 ${activeTab === 'sales' ? 'border-turmeric-600 text-turmeric-700' : 'border-transparent text-stone-500'}`}
        >
          {t('accountant.sales_register')}
        </button>
        <button
          onClick={() => setActiveTab('gst')}
          className={`pb-2 px-3 text-xs font-bold border-b-2 ${activeTab === 'gst' ? 'border-turmeric-600 text-turmeric-700' : 'border-transparent text-stone-500'}`}
        >
          {t('accountant.gst_summary')}
        </button>
        <button
          onClick={() => setActiveTab('ageing')}
          className={`pb-2 px-3 text-xs font-bold border-b-2 ${activeTab === 'ageing' ? 'border-turmeric-600 text-turmeric-700' : 'border-transparent text-stone-500'}`}
        >
          {t('accountant.ageing_report')}
        </button>
      </div>

      {/* Content */}
      {activeTab === 'sales' && (
        <div className="bg-white dark:bg-stone-900 border border-stone-300 rounded overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-stone-100 font-bold border-b">
              <tr>
                <th className="p-2.5">Invoice No</th>
                <th className="p-2.5">Date</th>
                <th className="p-2.5">Customer</th>
                <th className="p-2.5">State</th>
                <th className="p-2.5 text-right">Subtotal</th>
                <th className="p-2.5 text-right">CGST</th>
                <th className="p-2.5 text-right">SGST</th>
                <th className="p-2.5 text-right">IGST</th>
                <th className="p-2.5 text-right">Total</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {salesData.map((d) => (
                <tr key={d.id} className="hover:bg-cream-50">
                  <td className="p-2.5 font-mono font-bold text-turmeric-700">{d.invoice_no}</td>
                  <td className="p-2.5">{d.invoice_date}</td>
                  <td className="p-2.5">{d.customer_name}</td>
                  <td className="p-2.5">{d.state}</td>
                  <td className="p-2.5 text-right">Rs {d.subtotal_rs}</td>
                  <td className="p-2.5 text-right">Rs {d.cgst_rs}</td>
                  <td className="p-2.5 text-right">Rs {d.sgst_rs}</td>
                  <td className="p-2.5 text-right">Rs {d.igst_rs}</td>
                  <td className="p-2.5 text-right font-bold">Rs {d.total_rs}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {activeTab === 'gst' && gstData && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div className="p-4 bg-white border border-stone-300 rounded">
            <h4 className="font-bold text-sm text-stone-900 mb-2">Tamil Nadu Intra-State (CGST + SGST)</h4>
            <div className="space-y-1">
              <div className="flex justify-between"><span>Taxable Value:</span><b>Rs {gstData.intra_state_supplies.taxable_value_rs}</b></div>
              <div className="flex justify-between"><span>CGST (2.5%):</span><b>Rs {gstData.intra_state_supplies.cgst_rs}</b></div>
              <div className="flex justify-between"><span>SGST (2.5%):</span><b>Rs {gstData.intra_state_supplies.sgst_rs}</b></div>
              <div className="flex justify-between border-t pt-1 font-bold"><span>Total Tax:</span><b>Rs {gstData.intra_state_supplies.total_tax_rs}</b></div>
            </div>
          </div>

          <div className="p-4 bg-white border border-stone-300 rounded">
            <h4 className="font-bold text-sm text-stone-900 mb-2">Inter-State Supplies (IGST)</h4>
            <div className="space-y-1">
              <div className="flex justify-between"><span>Taxable Value:</span><b>Rs {gstData.inter_state_supplies.taxable_value_rs}</b></div>
              <div className="flex justify-between"><span>IGST (5%):</span><b>Rs {gstData.inter_state_supplies.igst_rs}</b></div>
              <div className="flex justify-between border-t pt-1 font-bold"><span>Total Tax:</span><b>Rs {gstData.inter_state_supplies.total_tax_rs}</b></div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'ageing' && (
        <div className="bg-white border border-stone-300 rounded overflow-x-auto text-xs">
          <table className="w-full text-left">
            <thead className="bg-stone-100 font-bold border-b">
              <tr>
                <th className="p-2.5">Customer</th>
                <th className="p-2.5">State</th>
                <th className="p-2.5 text-right">Total Outstanding</th>
                <th className="p-2.5 text-right">0-30 Days</th>
                <th className="p-2.5 text-right">31-60 Days</th>
                <th className="p-2.5 text-right">61-90 Days</th>
                <th className="p-2.5 text-right">90+ Days</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {ageingData.map((a) => (
                <tr key={a.customer_id} className="hover:bg-cream-50">
                  <td className="p-2.5 font-bold">{a.customer_name}</td>
                  <td className="p-2.5">{a.state}</td>
                  <td className="p-2.5 text-right font-bold text-rose-700">Rs {a.total_outstanding_rs}</td>
                  <td className="p-2.5 text-right">Rs {a.bucket_0_30_rs}</td>
                  <td className="p-2.5 text-right">Rs {a.bucket_31_60_rs}</td>
                  <td className="p-2.5 text-right">Rs {a.bucket_61_90_rs}</td>
                  <td className="p-2.5 text-right">Rs {a.bucket_90_plus_rs}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
