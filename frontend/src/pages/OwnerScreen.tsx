import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';

export const OwnerScreen: React.FC<{ token: string; user: any; onSelectStock: (type: string, id: number) => void }> = ({ token, user, onSelectStock }) => {
  const { t } = useTranslation();
  const [data, setData] = useState<any | null>(null);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      const res = await fetch('/api/v1/dashboard/owner', {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) setData(await res.json());
    } catch {}
  };

  if (!data) return <div className="text-xs text-stone-500">Loading factory dashboard...</div>;

  return (
    <div className="space-y-6">
      {/* Authentic Market & Factory Status Banner */}
      <div className="relative overflow-hidden rounded-xl border border-stone-300 dark:border-stone-800 bg-stone-900 text-white shadow-md">
        <img
          src="/images/market_hero.jpg"
          alt="Sri Lakshmi Snacks Traditional Market Bazaar"
          className="w-full h-40 sm:h-48 object-cover object-center opacity-45"
        />
        <div className="absolute inset-0 bg-gradient-to-r from-black/95 via-black/75 to-transparent p-5 sm:p-6 flex flex-col justify-center">
          <div className="flex items-center gap-2 mb-1.5">
            <span className="text-[10px] font-bold uppercase tracking-wider bg-turmeric-600 text-white px-2 py-0.5 rounded shadow-xs">
              Executive Factory Overview
            </span>
            <span className="text-xs text-amber-300 font-medium">
              Tiruchirappalli Facility • Thuvakudi
            </span>
          </div>
          <h2 className="text-xl sm:text-2xl font-bold text-white">
            Sri Lakshmi Snacks • Operations & Audit
          </h2>
          <p className="text-xs text-stone-300 max-w-xl mt-1">
            Real-time visibility into production batches, raw material weighted-average costing, GST outward supplies, and retail market receivables across Tamil Nadu.
          </p>
        </div>
      </div>

      {/* Top 4 KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-4 bg-white dark:bg-stone-900 border border-stone-300 dark:border-stone-700 rounded shadow-sm">
          <span className="text-xs uppercase font-bold text-stone-500 block mb-1">Today's Orders</span>
          <div className="text-2xl font-bold text-stone-900 dark:text-white">
            Rs {data.today_orders.total_value_rs}
          </div>
          <span className="text-xs text-stone-500">{data.today_orders.count} orders booked today</span>
        </div>

        <div className="p-4 bg-white dark:bg-stone-900 border border-stone-300 dark:border-stone-700 rounded shadow-sm">
          <span className="text-xs uppercase font-bold text-stone-500 block mb-1">Finished Goods Stock</span>
          <div className="text-2xl font-bold text-turmeric-600">
            {data.inventory.finished_goods[0]?.balance_packets || 0} pkts
          </div>
          <button
            onClick={() => onSelectStock('finished_goods', 1)}
            className="text-xs underline text-turmeric-700 hover:text-turmeric-800"
          >
            Kai Murukku 200g (View Ledger)
          </button>
        </div>

        <div className="p-4 bg-white dark:bg-stone-900 border border-stone-300 dark:border-stone-700 rounded shadow-sm">
          <span className="text-xs uppercase font-bold text-stone-500 block mb-1">Total Outstanding Dues</span>
          <div className="text-2xl font-bold text-chilli-600">
            Rs {data.receivables.total_outstanding_rs}
          </div>
          <span className="text-xs text-stone-500">From {data.receivables.top_debtors.length} active customer(s)</span>
        </div>

        <div className="p-4 bg-white dark:bg-stone-900 border border-stone-300 dark:border-stone-700 rounded shadow-sm">
          <span className="text-xs uppercase font-bold text-stone-500 block mb-1">Cost Per Packet</span>
          <div className="text-2xl font-bold text-leaf-600">
            Rs {data.cost_per_packet_history[0]?.cost_per_packet_rs || '31.14'}
          </div>
          <span className="text-xs text-stone-500">Margin: ~37.7% vs Rs 50 MRP</span>
        </div>
      </div>

      {/* Production Variance Alerts */}
      {data.variance_alerts.length > 0 && (
        <div className="p-4 bg-amber-50 border border-amber-300 rounded shadow-sm">
          <h3 className="font-bold text-sm text-amber-900 mb-2">🚨 Live Production Variance Alerts</h3>
          <div className="space-y-1.5 text-xs text-amber-800">
            {data.variance_alerts.map((alert: any, idx: number) => (
              <div key={idx} className="flex items-center gap-2">
                <span className="font-bold uppercase text-[10px] bg-amber-200 px-1.5 py-0.5 rounded text-amber-900">
                  {alert.run_no}
                </span>
                <span>{alert.message}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Receivables & Top Debtors */}
      <div className="bg-white dark:bg-stone-900 border border-stone-300 rounded overflow-hidden shadow-sm">
        <div className="p-4 border-b">
          <h3 className="font-bold text-sm text-stone-900">Top Outstanding Receivables</h3>
        </div>
        <table className="w-full text-left text-xs">
          <thead className="bg-stone-100 font-bold border-b">
            <tr>
              <th className="p-3">Customer</th>
              <th className="p-3">State</th>
              <th className="p-3">Phone</th>
              <th className="p-3 text-right">Outstanding (Rs)</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {data.receivables.top_debtors.map((d: any) => (
              <tr key={d.customer_id} className="hover:bg-cream-50">
                <td className="p-3 font-semibold">{d.customer_name}</td>
                <td className="p-3">{d.state}</td>
                <td className="p-3 font-mono">{d.phone}</td>
                <td className="p-3 text-right font-bold text-rose-700">Rs {d.outstanding_rs}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
