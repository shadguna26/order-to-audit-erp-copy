import React, { useState, useEffect } from 'react';

interface RawMaterial {
  id: number;
  code: string;
  name: string;
  type: 'raw' | 'packaging';
  base_unit: 'g' | 'ml' | 'piece';
  unit_conversions?: Record<string, number> | null;
  reorder_level_base: number | string;
  is_active: boolean;
}

export const RawMaterialsManager: React.FC<{
  token: string;
  onCreated?: (rm: RawMaterial) => void;
}> = ({ token, onCreated }) => {
  const [materials, setMaterials] = useState<RawMaterial[]>([]);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState<{ text: string; type: 'success' | 'error' } | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState<RawMaterial | null>(null);

  const [name, setName] = useState('');
  const [code, setCode] = useState('');
  const [matType, setMatType] = useState<'raw' | 'packaging'>('raw');
  const [baseUnit, setBaseUnit] = useState<'g' | 'ml' | 'piece'>('g');
  const [convText, setConvText] = useState('{"kg": 1000}');
  const [reorderLevel, setReorderLevel] = useState('0');
  const [isActive, setIsActive] = useState(true);
  const [openingStock, setOpeningStock] = useState('');
  const [openingCostPaise, setOpeningCostPaise] = useState('0');
  const [batchNo, setBatchNo] = useState('');
  const [expiryDate, setExpiryDate] = useState('');

  useEffect(() => {
    loadMaterials();
  }, []);

  const loadMaterials = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/v1/raw-materials?include_inactive=true', {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) setMaterials(await res.json());
    } finally {
      setLoading(false);
    }
  };

  const openCreate = () => {
    setEditing(null);
    setName('');
    setCode('');
    setMatType('raw');
    setBaseUnit('g');
    setConvText('{"kg": 1000}');
    setReorderLevel('0');
    setIsActive(true);
    setOpeningStock('');
    setOpeningCostPaise('0');
    setBatchNo('');
    setExpiryDate('');
    setShowModal(true);
  };

  const openEdit = (rm: RawMaterial) => {
    setEditing(rm);
    setName(rm.name);
    setCode(rm.code);
    setMatType(rm.type);
    setBaseUnit(rm.base_unit);
    setConvText(rm.unit_conversions ? JSON.stringify(rm.unit_conversions) : '');
    setReorderLevel(String(rm.reorder_level_base ?? 0));
    setIsActive(rm.is_active);
    setShowModal(true);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setMsg(null);
    let parsedConv: Record<string, number> | undefined;
    if (convText.trim()) {
      try {
        parsedConv = JSON.parse(convText);
      } catch {
        setMsg({ text: 'Unit conversions must be valid JSON (e.g. {"kg": 1000})', type: 'error' });
        return;
      }
    }

    try {
      if (editing) {
        const res = await fetch(`/api/v1/raw-materials/${editing.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
          body: JSON.stringify({
            name,
            type: matType,
            base_unit: baseUnit,
            unit_conversions: parsedConv,
            reorder_level_base: Number(reorderLevel || 0),
            is_active: isActive,
          }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Update failed');
        setMsg({ text: `Updated ${data.name}`, type: 'success' });
      } else {
        const payload: any = {
          name,
          code: code.trim() || undefined,
          type: matType,
          base_unit: baseUnit,
          unit_conversions: parsedConv,
          reorder_level_base: Number(reorderLevel || 0),
        };
        if (openingStock && Number(openingStock) > 0) {
          payload.opening_stock_base = Number(openingStock);
          payload.opening_unit_cost_paise = Number(openingCostPaise || 0);
          if (batchNo.trim()) payload.batch_no = batchNo.trim();
          if (expiryDate) payload.expiry_date = expiryDate;
        }
        const res = await fetch('/api/v1/raw-materials', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
          body: JSON.stringify(payload),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Create failed');
        setMsg({ text: `Added ${data.name} (${data.code})`, type: 'success' });
        if (onCreated) onCreated(data);
      }
      setShowModal(false);
      loadMaterials();
    } catch (err: any) {
      setMsg({ text: err.message || 'Error saving raw material', type: 'error' });
    }
  };

  return (
    <div className="space-y-4">
      {msg && (
        <div
          className={`p-3 rounded text-xs ${
            msg.type === 'success'
              ? 'bg-emerald-50 text-emerald-800 border border-emerald-300'
              : 'bg-rose-50 text-rose-800 border border-rose-300'
          }`}
        >
          {msg.text}
        </div>
      )}

      <div className="flex justify-between items-center bg-white dark:bg-stone-900 border border-stone-300 dark:border-stone-700 p-4 rounded">
        <div>
          <h3 className="text-sm font-bold text-stone-900 dark:text-white">Raw & Packaging Materials</h3>
          <p className="text-xs text-stone-500">Manage raw ingredients, packaging units, conversions, and opening balances.</p>
        </div>
        <button
          onClick={openCreate}
          className="min-h-[40px] px-4 bg-turmeric-600 hover:bg-turmeric-700 text-white font-bold text-xs rounded"
        >
          + Add Raw Material
        </button>
      </div>

      <div className="bg-white dark:bg-stone-900 border border-stone-300 dark:border-stone-700 rounded overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead className="bg-stone-100 dark:bg-stone-800 border-b border-stone-200 font-bold">
            <tr>
              <th className="p-3">Code</th>
              <th className="p-3">Name</th>
              <th className="p-3">Type</th>
              <th className="p-3">Base Unit</th>
              <th className="p-3">Reorder Level</th>
              <th className="p-3">Status</th>
              <th className="p-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-stone-200 dark:divide-stone-800">
            {loading && (
              <tr>
                <td colSpan={7} className="p-4 text-center text-stone-500">Loading...</td>
              </tr>
            )}
            {!loading &&
              materials.map((rm) => (
                <tr key={rm.id} className="hover:bg-cream-50 dark:hover:bg-stone-800/50">
                  <td className="p-3 font-mono font-semibold text-turmeric-700">{rm.code}</td>
                  <td className="p-3 font-semibold">{rm.name}</td>
                  <td className="p-3 uppercase text-[10px] font-bold">{rm.type}</td>
                  <td className="p-3">{rm.base_unit}</td>
                  <td className="p-3">{rm.reorder_level_base} {rm.base_unit}</td>
                  <td className="p-3">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                        rm.is_active ? 'bg-emerald-100 text-emerald-800' : 'bg-stone-200 text-stone-600'
                      }`}
                    >
                      {rm.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="p-3 text-right">
                    <button
                      onClick={() => openEdit(rm)}
                      className="px-2.5 py-1 bg-stone-200 dark:bg-stone-700 font-semibold rounded hover:bg-stone-300 text-xs"
                    >
                      Edit
                    </button>
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <form
            onSubmit={handleSave}
            className="bg-white dark:bg-stone-900 border border-stone-300 dark:border-stone-700 rounded max-w-lg w-full p-5 space-y-3 max-h-[90vh] overflow-y-auto"
          >
            <h3 className="font-bold text-base text-stone-900 dark:text-white">
              {editing ? `Edit ${editing.name}` : 'Add New Raw / Packaging Material'}
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              <div>
                <label className="block font-semibold mb-1">Material Name *</label>
                <input
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full min-h-[38px] px-3 border border-stone-300 rounded bg-white dark:bg-stone-800"
                  placeholder="e.g. Black Pepper"
                />
              </div>
              <div>
                <label className="block font-semibold mb-1">Code (blank = auto)</label>
                <input
                  value={code}
                  disabled={!!editing}
                  onChange={(e) => setCode(e.target.value)}
                  className="w-full min-h-[38px] px-3 border border-stone-300 rounded bg-white dark:bg-stone-800 disabled:opacity-60"
                  placeholder="RM-PEPPER"
                />
              </div>
              <div>
                <label className="block font-semibold mb-1">Type</label>
                <select
                  value={matType}
                  onChange={(e) => setMatType(e.target.value as 'raw' | 'packaging')}
                  className="w-full min-h-[38px] px-3 border border-stone-300 rounded bg-white dark:bg-stone-800"
                >
                  <option value="raw">Raw Ingredient</option>
                  <option value="packaging">Packaging Material</option>
                </select>
              </div>
              <div>
                <label className="block font-semibold mb-1">Base Unit</label>
                <select
                  value={baseUnit}
                  onChange={(e) => setBaseUnit(e.target.value as 'g' | 'ml' | 'piece')}
                  className="w-full min-h-[38px] px-3 border border-stone-300 rounded bg-white dark:bg-stone-800"
                >
                  <option value="g">Grams (g)</option>
                  <option value="ml">Millilitres (ml)</option>
                  <option value="piece">Pieces (piece)</option>
                </select>
              </div>
              <div>
                <label className="block font-semibold mb-1">Reorder Level (base unit)</label>
                <input
                  type="number"
                  min="0"
                  value={reorderLevel}
                  onChange={(e) => setReorderLevel(e.target.value)}
                  className="w-full min-h-[38px] px-3 border border-stone-300 rounded bg-white dark:bg-stone-800"
                />
              </div>
              <div>
                <label className="block font-semibold mb-1">Unit Conversions (JSON)</label>
                <input
                  value={convText}
                  onChange={(e) => setConvText(e.target.value)}
                  className="w-full min-h-[38px] px-3 border border-stone-300 rounded bg-white dark:bg-stone-800 font-mono"
                  placeholder='{"kg": 1000}'
                />
              </div>
            </div>

            {!editing && (
              <div className="border-t border-stone-200 pt-3 space-y-2 text-xs">
                <div className="font-bold text-stone-700 dark:text-stone-300">
                  Optional Opening Stock (posts to stock_ledger as opening_balance)
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  <div>
                    <label className="block font-semibold mb-1">Qty ({baseUnit})</label>
                    <input
                      type="number"
                      min="0"
                      value={openingStock}
                      onChange={(e) => setOpeningStock(e.target.value)}
                      className="w-full min-h-[36px] px-2 border border-stone-300 rounded bg-white dark:bg-stone-800"
                    />
                  </div>
                  <div>
                    <label className="block font-semibold mb-1">Cost (paise/unit)</label>
                    <input
                      type="number"
                      min="0"
                      value={openingCostPaise}
                      onChange={(e) => setOpeningCostPaise(e.target.value)}
                      className="w-full min-h-[36px] px-2 border border-stone-300 rounded bg-white dark:bg-stone-800"
                    />
                  </div>
                  <div>
                    <label className="block font-semibold mb-1">Batch No</label>
                    <input
                      value={batchNo}
                      onChange={(e) => setBatchNo(e.target.value)}
                      className="w-full min-h-[36px] px-2 border border-stone-300 rounded bg-white dark:bg-stone-800"
                    />
                  </div>
                  <div>
                    <label className="block font-semibold mb-1">Expiry Date</label>
                    <input
                      type="date"
                      value={expiryDate}
                      onChange={(e) => setExpiryDate(e.target.value)}
                      className="w-full min-h-[36px] px-2 border border-stone-300 rounded bg-white dark:bg-stone-800"
                    />
                  </div>
                </div>
              </div>
            )}

            {editing && (
              <label className="flex items-center gap-2 text-xs font-semibold">
                <input type="checkbox" checked={isActive} onChange={(e) => setIsActive(e.target.checked)} />
                Active
              </label>
            )}

            <div className="flex gap-2 pt-2">
              <button
                type="button"
                onClick={() => setShowModal(false)}
                className="flex-1 min-h-[40px] border border-stone-300 rounded text-xs font-semibold"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="flex-1 min-h-[40px] bg-leaf-600 hover:bg-leaf-700 text-white font-bold rounded text-xs"
              >
                {editing ? 'Save Changes' : 'Create Material'}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};
