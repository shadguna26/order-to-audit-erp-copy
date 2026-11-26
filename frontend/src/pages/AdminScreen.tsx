import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { downloadFile, shareFile } from '../lib/download';
import { ProductsManager } from '../components/ProductsManager';
import { RawMaterialsManager } from '../components/RawMaterialsManager';

export const AdminScreen: React.FC<{ token: string; user: any; onSelectStock: (type: string, id: number) => void }> = ({ token, user, onSelectStock }) => {
  const { t } = useTranslation();
  const [orders, setOrders] = useState<any[]>([]);
  const [invoices, setInvoices] = useState<any[]>([]);
  const [customers, setCustomers] = useState<any[]>([]);

  // Dispatch modal
  const [selectedInvoiceForDispatch, setSelectedInvoiceForDispatch] = useState<any | null>(null);
  const [vehicleNo, setVehicleNo] = useState('TN-45-AT-1234');

  // Payment modal
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [paymentCustomerId, setPaymentCustomerId] = useState(1);
  const [paymentAmountPaise, setPaymentAmountPaise] = useState(400000); // Rs 4,000

  const [msg, setMsg] = useState<{ text: string; type: 'success' | 'error' } | null>(null);
  const [downloadError, setDownloadError] = useState<string | null>(null);
  const [downloadingId, setDownloadingId] = useState<number | null>(null);
  const [sharingId, setSharingId] = useState<number | null>(null);
  const [activeTab, setActiveTab] = useState<'desk' | 'products' | 'materials'>('desk');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const ordRes = await fetch('/api/v1/orders', { headers: { Authorization: `Bearer ${token}` } });
      if (ordRes.ok) setOrders(await ordRes.json());

      const invRes = await fetch('/api/v1/invoices', { headers: { Authorization: `Bearer ${token}` } });
      if (invRes.ok) setInvoices(await invRes.json());
    } catch {}
  };

  const approveOrder = async (orderId: number) => {
    try {
      const res = await fetch(`/api/v1/orders/${orderId}/approve`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Failed to approve');
      setMsg({ text: 'Order approved successfully!', type: 'success' });
      loadData();
    } catch (e: any) {
      setMsg({ text: e.message, type: 'error' });
    }
  };

  const generateInvoice = async (orderId: number) => {
    try {
      const res = await fetch(`/api/v1/invoices/from-order/${orderId}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Failed to create invoice');
      setMsg({ text: 'GST Tax Invoice created!', type: 'success' });
      loadData();
    } catch (e: any) {
      setMsg({ text: e.message, type: 'error' });
    }
  };

  const submitDispatch = async () => {
    if (!selectedInvoiceForDispatch) return;
    try {
      const res = await fetch('/api/v1/dispatches', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ invoice_id: selectedInvoiceForDispatch.id, vehicle_no: vehicleNo })
      });
      if (!res.ok) throw new Error('Dispatch failed');
      setMsg({ text: 'Dispatch recorded. Finished goods deducted from ledger!', type: 'success' });
      setSelectedInvoiceForDispatch(null);
      loadData();
    } catch (e: any) {
      setMsg({ text: e.message, type: 'error' });
    }
  };

  const submitPayment = async () => {
    try {
      const res = await fetch('/api/v1/payments', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          customer_id: paymentCustomerId,
          amount_paise: paymentAmountPaise,
          payment_mode: 'upi'
        })
      });
      if (!res.ok) throw new Error('Payment failed');
      setMsg({ text: `Payment of Rs ${paymentAmountPaise / 100} recorded successfully!`, type: 'success' });
      setShowPaymentModal(false);
    } catch (e: any) {
      setMsg({ text: e.message, type: 'error' });
    }
  };

  const handleDownloadPdf = async (invId: number, invNo: string) => {
    try {
      setDownloadError(null);
      setDownloadingId(invId);
      const cleanNo = invNo.replace(/[/\\:*?"<>|]/g, '-');
      await downloadFile(`/api/v1/invoices/${invId}/pdf`, `${cleanNo}.pdf`, token);
    } catch (e: any) {
      setDownloadError(`${t('common.download_failed')} (${e.message || 'Error'})`);
    } finally {
      setDownloadingId(null);
    }
  };

  const handleShareWhatsApp = async (invId: number, invNo: string, waUrl: string) => {
    try {
      setDownloadError(null);
      setSharingId(invId);
      const cleanNo = invNo.replace(/[/\\:*?"<>|]/g, '-');
      await shareFile(
        `/api/v1/invoices/${invId}/pdf`,
        `${cleanNo}.pdf`,
        `Invoice ${invNo} from Sri Lakshmi Snacks`,
        token
      );
    } catch (_e) {
      // Final fallback: open the wa.me URL they already have
      if (waUrl) window.open(waUrl, '_blank', 'noopener,noreferrer');
    } finally {
      setSharingId(null);
    }
  };

  return (
    <div data-no-fx="true" className="space-y-6">
      {/* Admin Sub-Navigation */}
      <div className="flex gap-2 border-b border-stone-200 dark:border-stone-700">
        <button
          onClick={() => setActiveTab('desk')}
          className={`pb-2 px-3 text-xs font-bold border-b-2 ${activeTab === 'desk' ? 'border-turmeric-600 text-turmeric-700' : 'border-transparent text-stone-500'}`}
        >
          Orders & Billing
        </button>
        <button
          onClick={() => setActiveTab('products')}
          className={`pb-2 px-3 text-xs font-bold border-b-2 ${activeTab === 'products' ? 'border-turmeric-600 text-turmeric-700' : 'border-transparent text-stone-500'}`}
        >
          Products & Recipes (BOM)
        </button>
        <button
          onClick={() => setActiveTab('materials')}
          className={`pb-2 px-3 text-xs font-bold border-b-2 ${activeTab === 'materials' ? 'border-turmeric-600 text-turmeric-700' : 'border-transparent text-stone-500'}`}
        >
          Raw & Packaging Materials
        </button>
      </div>

      {activeTab === 'products' && <ProductsManager token={token} />}
      {activeTab === 'materials' && <RawMaterialsManager token={token} />}
      {activeTab === 'desk' && (
        <>
      {msg && (
        <div className={`p-3 rounded text-xs ${msg.type === 'success' ? 'bg-emerald-50 text-emerald-800 border border-emerald-300' : 'bg-rose-50 text-rose-800 border border-rose-300'}`}>
          {msg.text}
        </div>
      )}
      {downloadError && (
        <div className="p-3 rounded text-xs bg-rose-50 text-rose-800 border border-rose-300">
          ⚠️ {downloadError}
        </div>
      )}

      {/* Top Action Bar */}
      <div className="flex justify-between items-center bg-white dark:bg-stone-900 border border-stone-300 dark:border-stone-700 p-4 rounded">
        <div>
          <h2 className="text-base font-bold text-stone-900 dark:text-white">Admin Order & Billing Desk</h2>
          <p className="text-xs text-stone-500">Approve incoming orders, post invoices, and dispatch vehicles.</p>
        </div>
        <button
          onClick={() => setShowPaymentModal(true)}
          className="min-h-[44px] px-4 bg-leaf-600 hover:bg-leaf-700 text-white font-bold text-xs rounded shadow-sm"
        >
          + Record Payment
        </button>
      </div>

      {/* Orders Table */}
      <div className="bg-white dark:bg-stone-900 border border-stone-300 dark:border-stone-700 rounded overflow-hidden">
        <div className="p-4 border-b border-stone-200 dark:border-stone-800">
          <h3 className="font-bold text-sm text-stone-900 dark:text-white">Sales Orders</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead className="bg-stone-100 dark:bg-stone-800 border-b border-stone-200 font-bold">
              <tr>
                <th className="p-3">Order No</th>
                <th className="p-3">Customer ID</th>
                <th className="p-3">Status</th>
                <th className="p-3">Date</th>
                <th className="p-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-stone-200 dark:divide-stone-800">
              {orders.map((o) => (
                <tr key={o.id} className="hover:bg-cream-50 dark:hover:bg-stone-800/50">
                  <td className="p-3 font-semibold">{o.order_no}</td>
                  <td className="p-3">Customer #{o.customer_id}</td>
                  <td className="p-3">
                    <span className="px-2 py-0.5 rounded uppercase font-bold text-[10px] bg-stone-100 text-stone-700">
                      {o.status}
                    </span>
                  </td>
                  <td className="p-3">{new Date(o.created_at).toLocaleDateString()}</td>
                  <td className="p-3 text-right space-x-2">
                    {o.status === 'submitted' && (
                      <button
                        onClick={() => approveOrder(o.id)}
                        className="px-2.5 py-1 bg-turmeric-600 text-white font-bold rounded hover:bg-turmeric-700"
                      >
                        Approve
                      </button>
                    )}
                    {o.status === 'approved' && (
                      <button
                        onClick={() => generateInvoice(o.id)}
                        className="px-2.5 py-1 bg-leaf-600 text-white font-bold rounded hover:bg-leaf-700"
                      >
                        Create Invoice
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Invoices Table */}
      <div className="bg-white dark:bg-stone-900 border border-stone-300 dark:border-stone-700 rounded overflow-hidden">
        <div className="p-4 border-b border-stone-200 dark:border-stone-800">
          <h3 className="font-bold text-sm text-stone-900 dark:text-white">Posted GST Tax Invoices</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead className="bg-stone-100 dark:bg-stone-800 border-b border-stone-200 font-bold">
              <tr>
                <th className="p-3">Invoice No</th>
                <th className="p-3">Customer ID</th>
                <th className="p-3">Total (Rs)</th>
                <th className="p-3">Status</th>
                <th className="p-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-stone-200 dark:divide-stone-800">
              {invoices.map((inv) => (
                <tr key={inv.id} className="hover:bg-cream-50 dark:hover:bg-stone-800/50">
                  <td className="p-3 font-semibold font-mono text-turmeric-700">{inv.invoice_no}</td>
                  <td className="p-3">Customer #{inv.customer_id}</td>
                  <td className="p-3 font-bold">Rs {(inv.total_paise / 100).toFixed(2)}</td>
                  <td className="p-3">
                    <span className="px-2 py-0.5 rounded uppercase font-bold text-[10px] bg-emerald-100 text-emerald-800">
                      {inv.status}
                    </span>
                  </td>
                  <td className="p-3 text-right space-x-2">
                    <button
                      onClick={() => handleDownloadPdf(inv.id, inv.invoice_no)}
                      disabled={downloadingId === inv.id}
                      className="px-2.5 py-1 bg-stone-200 dark:bg-stone-700 font-semibold rounded hover:bg-stone-300 dark:hover:bg-stone-600 text-xs disabled:opacity-50"
                    >
                      {downloadingId === inv.id ? t('common.downloading') : 'PDF'}
                    </button>
                    {inv.whatsapp_share_url && (
                      <button
                        onClick={() => handleShareWhatsApp(inv.id, inv.invoice_no, inv.whatsapp_share_url)}
                        disabled={sharingId === inv.id}
                        className="px-2.5 py-1 bg-emerald-600 text-white font-semibold rounded hover:bg-emerald-700 text-xs disabled:opacity-50"
                      >
                        {sharingId === inv.id ? t('common.sharing') : 'WhatsApp'}
                      </button>
                    )}
                    <button
                      onClick={() => setSelectedInvoiceForDispatch(inv)}
                      className="px-2.5 py-1 bg-stone-800 text-white font-bold rounded hover:bg-stone-900 text-xs"
                    >
                      Dispatch
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Dispatch Modal */}
      {selectedInvoiceForDispatch && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-stone-900 border border-stone-300 rounded max-w-md w-full p-6 space-y-4">
            <h3 className="font-bold text-base text-stone-900 dark:text-white">Record Vehicle Dispatch</h3>
            <p className="text-xs text-stone-500">
              Dispatching Invoice <b>{selectedInvoiceForDispatch.invoice_no}</b> will deduct finished goods from the stock ledger.
            </p>
            <div>
              <label className="block text-xs font-semibold mb-1">Vehicle Number</label>
              <input
                type="text"
                value={vehicleNo}
                onChange={(e) => setVehicleNo(e.target.value)}
                className="w-full min-h-[44px] px-3 border border-stone-300 rounded text-sm bg-white dark:bg-stone-800"
              />
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setSelectedInvoiceForDispatch(null)}
                className="flex-1 min-h-[44px] border border-stone-300 rounded text-xs font-semibold"
              >
                Cancel
              </button>
              <button
                onClick={submitDispatch}
                className="flex-1 min-h-[44px] bg-turmeric-600 text-white font-bold rounded text-xs"
              >
                Confirm Dispatch
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Payment Modal */}
      {showPaymentModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-stone-900 border border-stone-300 rounded max-w-md w-full p-6 space-y-4">
            <h3 className="font-bold text-base text-stone-900 dark:text-white">Record Customer Payment</h3>
            <div>
              <label className="block text-xs font-semibold mb-1">Customer</label>
              <select
                value={paymentCustomerId}
                onChange={(e) => setPaymentCustomerId(Number(e.target.value))}
                className="w-full min-h-[44px] px-3 border border-stone-300 rounded text-sm bg-white dark:bg-stone-800"
              >
                <option value={1}>Retailer A (Sri Balaji Provision Stores)</option>
                <option value={2}>Distributor B (Cauvery Sweets & Snacks)</option>
                <option value={3}>Retailer C (Murugan Maligai)</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold mb-1">Amount (Rupees)</label>
              <input
                type="number"
                value={paymentAmountPaise / 100}
                onChange={(e) => setPaymentAmountPaise(Number(e.target.value) * 100)}
                className="w-full min-h-[44px] px-3 border border-stone-300 rounded text-sm bg-white dark:bg-stone-800"
              />
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setShowPaymentModal(false)}
                className="flex-1 min-h-[44px] border border-stone-300 rounded text-xs font-semibold"
              >
                Cancel
              </button>
              <button
                onClick={submitPayment}
                className="flex-1 min-h-[44px] bg-leaf-600 text-white font-bold rounded text-xs"
              >
                Save Payment
              </button>
            </div>
          </div>
        </div>
      )}
        </>
      )}
    </div>
  );
};
