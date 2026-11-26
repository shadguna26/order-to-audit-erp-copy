import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { GuideHelper } from '../components/GuideHelper.jsx';
import { RawMaterialsManager } from '../components/RawMaterialsManager';

export const ProductionScreen: React.FC<{ token: string; user: any; onSelectStock: (type: string, id: number) => void }> = ({ token, user, onSelectStock }) => {
  const { t } = useTranslation();
  const [plans, setPlans] = useState<any[]>([]);
  const [prefill, setPrefill] = useState<any | null>(null);

  const [actualGood, setActualGood] = useState<number>(188);
  const [damagedPouches, setDamagedPouches] = useState<number>(6);
  const [cartonsUsed, setCartonsUsed] = useState<number>(9);
  const [issuedOil, setIssuedOil] = useState<number>(10500); // 10.5 L
  const [issuedFlour, setIssuedFlour] = useState<number>(40000); // 40 kg

  const [msg, setMsg] = useState<{ text: string; type: 'success' | 'error' } | null>(null);
  const [prodStep, setProdStep] = useState<'output' | 'issue' | 'save'>('output');
  const [activeTab, setActiveTab] = useState<'runs' | 'materials'>('runs');

  useEffect(() => {
    loadPlanning();
    loadPrefill();
  }, []);

  const loadPlanning = async () => {
    try {
      const res = await fetch('/api/v1/production/plan-from-orders', {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) setPlans(await res.json());
    } catch { }
  };

  const loadPrefill = async () => {
    try {
      const res = await fetch('/api/v1/production/prefill/1?batches=1', {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) setPrefill(await res.json());
    } catch { }
  };

  const handleSaveRun = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const runPayload = {
        product_id: 1,
        bom_id: 1,
        planned_batches: 1,
        actual_good_output_packets: actualGood,
        actual_damaged_pouches: damagedPouches,
        actual_cartons_used: cartonsUsed,
        issued_items: [
          { raw_material_id: 1, actual_qty_base: issuedFlour }, // Flour
          { raw_material_id: 2, actual_qty_base: issuedOil },   // Oil
          { raw_material_id: 3, actual_qty_base: 1200.0 },      // Spice
          { raw_material_id: 4, actual_qty_base: actualGood + damagedPouches }, // Pouches
          { raw_material_id: 5, actual_qty_base: cartonsUsed }, // Cartons
        ],
        overheads: [
          { overhead_type: 'labour', amount_paise: 120000 },
          { overhead_type: 'gas_power', amount_paise: 60000 }
        ]
      };

      const res = await fetch('/api/v1/production/runs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify(runPayload)
      });

      if (!res.ok) throw new Error('Failed to record production run');
      const data = await res.json();
      setMsg({
        text: `Run ${data.run_no} posted! Cost: Rs ${(data.cost_per_packet_paise / 100).toFixed(2)}/pkt (Yield Var: ${data.yield_variance_pct}%)`,
        type: 'success'
      });
      loadPlanning();
    } catch (err: any) {
      setMsg({ text: err.message, type: 'error' });
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex gap-2 border-b border-stone-200 dark:border-stone-700">
        <button
          onClick={() => setActiveTab('runs')}
          className={`pb-2 px-3 text-xs font-bold border-b-2 ${activeTab === 'runs' ? 'border-turmeric-600 text-turmeric-700' : 'border-transparent text-stone-500'}`}
        >
          Production Runs
        </button>
        <button
          onClick={() => setActiveTab('materials')}
          className={`pb-2 px-3 text-xs font-bold border-b-2 ${activeTab === 'materials' ? 'border-turmeric-600 text-turmeric-700' : 'border-transparent text-stone-500'}`}
        >
          Raw & Packaging Materials
        </button>
      </div>

      {activeTab === 'materials' && <RawMaterialsManager token={token} />}
      {activeTab === 'runs' && (
        <>
      {msg && (
        <div className={`p-3 rounded text-xs ${msg.type === 'success' ? 'bg-emerald-50 text-emerald-800 border border-emerald-300' : 'bg-rose-50 text-rose-800 border border-rose-300'}`}>
          {msg.text}
        </div>
      )}

      {/* Production Planning from Pending Orders Banner */}
      <div className="bg-amber-50 border border-amber-300 rounded p-4">
        <h3 className="font-bold text-sm text-amber-900 mb-2">
          {t('production.planning_title')}
        </h3>
        {plans.length === 0 ? (
          <p className="text-xs text-amber-800">All approved orders have sufficient finished goods stock.</p>
        ) : (
          <div className="space-y-2 text-xs">
            {plans.map((p) => (
              <div key={p.product_id} className="p-3 bg-white dark:bg-stone-900 rounded border border-amber-200">
                <div className="font-bold text-stone-900 dark:text-white">
                  {p.product_name}: {p.recommendation}
                </div>
                <div className="text-stone-500 mt-1">
                  Approved Demand: {p.approved_demand_packets} pkts | Current Stock: {p.current_stock_packets} pkts | Net Shortfall: {p.net_shortfall_packets} pkts
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Production Run Execution Form */}
      <div className="bg-white dark:bg-stone-900 border border-stone-300 dark:border-stone-700 rounded p-6 shadow-sm">
        <div className="flex justify-between items-center border-b border-stone-200 pb-3 mb-4">
          <div>
            <h2 className="text-base font-bold text-stone-900 dark:text-white">{t('production.title')}</h2>
            <p className="text-xs text-stone-500">Post batch consumption and output atomically into the stock ledger.</p>
          </div>
          <span className="text-xs font-mono bg-turmeric-100 text-turmeric-800 px-2 py-1 rounded">
            Kai Murukku 200g (1 Batch = 200 pkts)
          </span>
        </div>

        <form onSubmit={handleSaveRun} className="space-y-5">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div data-guide="prod-output">
              <label className="block text-xs font-semibold mb-1">{t('production.actual_good_output')}</label>
              <input
                type="number"
                value={actualGood}
                onChange={(e) => {
                  setActualGood(Number(e.target.value));
                  setProdStep('issue');
                }}
                className="w-full min-h-[44px] px-3 border border-stone-300 rounded text-sm bg-white dark:bg-stone-800"
                required
              />
            </div>
            <div>
              <label className="block text-xs font-semibold mb-1">{t('production.damaged_pouches')}</label>
              <input
                type="number"
                value={damagedPouches}
                onChange={(e) => setDamagedPouches(Number(e.target.value))}
                className="w-full min-h-[44px] px-3 border border-stone-300 rounded text-sm bg-white dark:bg-stone-800"
                required
              />
            </div>
            <div>
              <label className="block text-xs font-semibold mb-1">{t('production.cartons_used')}</label>
              <input
                type="number"
                value={cartonsUsed}
                onChange={(e) => setCartonsUsed(Number(e.target.value))}
                className="w-full min-h-[44px] px-3 border border-stone-300 rounded text-sm bg-white dark:bg-stone-800"
                required
              />
            </div>
          </div>

          <div data-guide="prod-issue" className="border border-stone-200 dark:border-stone-800 rounded p-4 bg-stone-50 dark:bg-stone-800/40">
            <h4 className="text-xs font-bold text-stone-700 dark:text-stone-300 uppercase tracking-wider mb-3">
              Actual Issued Quantities
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold mb-1">Rice Flour (g) [Std: 40,000 g]</label>
                <input
                  type="number"
                  value={issuedFlour}
                  onChange={(e) => setIssuedFlour(Number(e.target.value))}
                  className="w-full min-h-[44px] px-3 border border-stone-300 rounded text-sm bg-white dark:bg-stone-800"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold mb-1">Sunflower Oil (ml) [Std: 10,000 ml]</label>
                <input
                  type="number"
                  value={issuedOil}
                  onChange={(e) => setIssuedOil(Number(e.target.value))}
                  className="w-full min-h-[44px] px-3 border border-stone-300 rounded text-sm bg-white dark:bg-stone-800"
                />
                <span className="text-[11px] text-amber-700 font-semibold block mt-1">
                  10,500 ml = +5.00% Variance (+0.5 L extra, about Rs 70)
                </span>
              </div>
            </div>
          </div>

          <button
            type="submit"
            data-guide="prod-save"
            className="w-full min-h-[48px] bg-turmeric-600 hover:bg-turmeric-700 text-white font-bold rounded text-sm shadow-sm"
          >
            {t('production.save_run')}
          </button>
        </form>
      </div>

      {/* Human Guide: Factory Production Master */}
      <GuideHelper
        target={
          prodStep === 'output'
            ? '[data-guide="prod-output"]'
            : prodStep === 'issue'
              ? '[data-guide="prod-issue"]'
              : '[data-guide="prod-save"]'
        }
        role="worker"
        guideKey={`prod_flow_${prodStep}`}
        messageKey={
          prodStep === 'output'
            ? 'guide.prod_output'
            : prodStep === 'issue'
              ? 'guide.prod_issue'
              : 'guide.prod_save'
        }
        side="top"
        idleSeconds={6}
        hasError={Boolean(msg && msg.type === 'error')}
        onGotIt={() => {
          if (prodStep === 'output') setProdStep('issue');
          else if (prodStep === 'issue') setProdStep('save');
        }}
      />
        </>
      )}
    </div>
  );
};
