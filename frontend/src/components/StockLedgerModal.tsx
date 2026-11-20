import React, { useState, useEffect } from 'react';

export const StockLedgerModal: React.FC<{
  isOpen: boolean;
  onClose: () => void;
  itemType: string;
  itemId: number;
  token: string;
}> = ({ isOpen, onClose, itemType, itemId, token }) => {
  const [entries, setEntries] = useState<any[]>([]);

  useEffect(() => {
    if (isOpen) {
      loadLedger();
    }
  }, [isOpen, itemType, itemId]);

  const loadLedger = async () => {
    try {
      const res = await fetch(`/api/v1/stock/ledger?item_type=${itemType}&item_id=${itemId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) setEntries(await res.json());
    } catch {}
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="bg-white dark:bg-stone-900 border border-stone-300 rounded max-w-3xl w-full p-6 space-y-4 max-h-[85vh] flex flex-col">
        <div className="flex justify-between items-center border-b pb-3">
          <div>
            <h3 className="font-bold text-base text-stone-900 dark:text-white">
              Immutable Stock Ledger (Source of Truth)
            </h3>
            <p className="text-xs text-stone-500">
              Every row is append-only. Balances are calculated dynamically via SUM.
            </p>
          </div>
          <button onClick={onClose} className="text-stone-400 hover:text-stone-700 font-bold text-lg">
            ✕
          </button>
        </div>

        <div className="overflow-y-auto flex-1">
          <table className="w-full text-left text-xs border-collapse">
            <thead className="bg-stone-100 font-bold border-b sticky top-0">
              <tr>
                <th className="p-2.5">Date & Time</th>
                <th className="p-2.5">Source Doc</th>
                <th className="p-2.5">Doc ID</th>
                <th className="p-2.5">Direction</th>
                <th className="p-2.5 text-right">Quantity (Base)</th>
                <th className="p-2.5">Location</th>
                <th className="p-2.5 text-right">Valuation (Paise)</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {entries.map((e) => (
                <tr key={e.id} className="hover:bg-cream-50 font-mono">
                  <td className="p-2.5">{new Date(e.created_at).toLocaleString()}</td>
                  <td className="p-2.5 uppercase font-bold text-stone-700">{e.source_doc_type}</td>
                  <td className="p-2.5">#{e.source_doc_id}</td>
                  <td className="p-2.5">
                    <span className={`px-1.5 py-0.5 rounded font-bold text-[10px] ${e.direction === 'IN' ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'}`}>
                      {e.direction}
                    </span>
                  </td>
                  <td className="p-2.5 text-right font-bold">{parseFloat(e.qty_base).toLocaleString()} {e.base_unit}</td>
                  <td className="p-2.5 uppercase">{e.location_type}</td>
                  <td className="p-2.5 text-right">{e.unit_cost_paise}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="border-t pt-3 flex justify-end">
          <button onClick={onClose} className="px-4 py-2 bg-stone-800 text-white font-bold text-xs rounded">
            Close Ledger Trace
          </button>
        </div>
      </div>
    </div>
  );
};
