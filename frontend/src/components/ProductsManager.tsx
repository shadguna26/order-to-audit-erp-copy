import React, { useState, useEffect } from 'react';

interface RawMaterialOption {
  id: number;
  code: string;
  name: string;
  type: 'raw' | 'packaging';
  base_unit: 'g' | 'ml' | 'piece';
}

interface BOMRow {
  raw_material_id: number;
  standard_qty_base: string;
}

export const ProductsManager: React.FC<{ token: string }> = ({ token }) => {
  const [products, setProducts] = useState<any[]>([]);
  const [materials, setMaterials] = useState<RawMaterialOption[]>([]);
  const [search, setSearch] = useState('');
  const [msg, setMsg] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  // Add / Edit Product modal
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState<any | null>(null);
  const [name, setName] = useState('');
  const [nameTa, setNameTa] = useState('');
  const [voiceAliases, setVoiceAliases] = useState('');
  const [code, setCode] = useState('');
  const [category, setCategory] = useState('Snacks');
  const [packVal, setPackVal] = useState('200');
  const [packUnit, setPackUnit] = useState('g');
  const [packetsPerCarton, setPacketsPerCarton] = useState('20');
  const [priceRs, setPriceRs] = useState('50.00');
  const [gstRate, setGstRate] = useState('5.00');
  const [hsnCode, setHsnCode] = useState('21069099');
  const [shelfLife, setShelfLife] = useState('90');
  const [reorderPackets, setReorderPackets] = useState('20');
  const [isActive, setIsActive] = useState(true);
  const [effectiveFrom, setEffectiveFrom] = useState('');

  // Opening stock (create only)
  const [openingPackets, setOpeningPackets] = useState('');
  const [batchNo, setBatchNo] = useState('');
  const [expiryDate, setExpiryDate] = useState('');

  // BOM recipe
  const [expectedYield, setExpectedYield] = useState('200');
  const [bomRows, setBomRows] = useState<BOMRow[]>([]);

  // Inline new raw material inside BOM section
  const [showInlineRm, setShowInlineRm] = useState(false);
  const [newRmName, setNewRmName] = useState('');
  const [newRmType, setNewRmType] = useState<'raw' | 'packaging'>('raw');
  const [newRmUnit, setNewRmUnit] = useState<'g' | 'ml' | 'piece'>('g');

  // Duplicate modal
  const [dupSource, setDupSource] = useState<any | null>(null);
  const [dupName, setDupName] = useState('');
  const [dupNameTa, setDupNameTa] = useState('');
  const [dupPackVal, setDupPackVal] = useState('500');
  const [dupPackUnit, setDupPackUnit] = useState('g');
  const [dupPriceRs, setDupPriceRs] = useState('');
  const [dupOpening, setDupOpening] = useState('');

  useEffect(() => {
    loadAll();
  }, []);

  const loadAll = async () => {
    try {
      const [pRes, rmRes] = await Promise.all([
        fetch('/api/v1/products?include_inactive=true', { headers: { Authorization: `Bearer ${token}` } }),
        fetch('/api/v1/raw-materials', { headers: { Authorization: `Bearer ${token}` } }),
      ]);
      if (pRes.ok) setProducts(await pRes.json());
      if (rmRes.ok) setMaterials(await rmRes.json());
    } catch {}
  };

  const openCreate = () => {
    setEditing(null);
    setName('');
    setNameTa('');
    setVoiceAliases('');
    setCode('');
    setCategory('Snacks');
    setPackVal('200');
    setPackUnit('g');
    setPacketsPerCarton('20');
    setPriceRs('50.00');
    setGstRate('5.00');
    setHsnCode('21069099');
    setShelfLife('90');
    setReorderPackets('20');
    setIsActive(true);
    setOpeningPackets('');
    setBatchNo('');
    setExpiryDate('');
    setExpectedYield('200');
    setBomRows([]);
    setShowInlineRm(false);
    setShowModal(true);
  };

  const openEdit = (p: any) => {
    setEditing(p);
    setName(p.name);
    setNameTa(p.name_ta || '');
    setVoiceAliases(p.voice_aliases || '');
    setCode(p.code);
    setCategory(p.category || 'Snacks');
    setPackVal(String(p.pack_size_value ?? p.pack_size_g));
    setPackUnit(p.pack_size_unit || 'g');
    setPacketsPerCarton(String(p.packets_per_carton ?? 20));
    setPriceRs(((p.selling_price_paise ?? 5000) / 100).toFixed(2));
    setGstRate(String(p.gst_rate_pct ?? 5));
    setHsnCode(p.hsn_code || '21069099');
    setShelfLife(String(p.shelf_life_days ?? 90));
    setReorderPackets(String(p.reorder_level_packets ?? 0));
    setIsActive(p.is_active);
    setEffectiveFrom('');
    setExpectedYield(String(p.bom?.expected_yield_packets ?? 200));
    setBomRows(
      (p.bom?.items || []).map((it: any) => ({
        raw_material_id: it.raw_material_id,
        standard_qty_base: String(it.standard_qty_base),
      }))
    );
    setShowInlineRm(false);
    setShowModal(true);
  };

  const addBomRow = () => {
    if (materials.length === 0) return;
    setBomRows([...bomRows, { raw_material_id: materials[0].id, standard_qty_base: '1000' }]);
  };

  const handleInlineAddRm = async () => {
    if (!newRmName.trim()) return;
    try {
      const res = await fetch('/api/v1/raw-materials', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          name: newRmName.trim(),
          type: newRmType,
          base_unit: newRmUnit,
          reorder_level_base: 0,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to add raw material');
      setMaterials((prev) => [...prev, data]);
      setBomRows((prev) => [...prev, { raw_material_id: data.id, standard_qty_base: '1000' }]);
      setNewRmName('');
      setShowInlineRm(false);
    } catch (e: any) {
      setMsg({ text: e.message, type: 'error' });
    }
  };

  const handleSaveProduct = async (e: React.FormEvent) => {
    e.preventDefault();
    setMsg(null);
    if (!/^\d{4}(\d{2})?(\d{2})?$/.test(hsnCode.trim())) {
      setMsg({ text: 'HSN code must be 4, 6, or 8 digits.', type: 'error' });
      return;
    }
    const pricePaise = Math.round(Number(priceRs) * 100);
    if (!Number.isFinite(pricePaise) || pricePaise <= 0) {
      setMsg({ text: 'Selling price must be greater than 0.', type: 'error' });
      return;
    }

    const bomItemsPayload = bomRows
      .filter((r) => Number(r.standard_qty_base) > 0)
      .map((r) => ({
        raw_material_id: Number(r.raw_material_id),
        standard_qty_base: Number(r.standard_qty_base),
      }));

    try {
      if (editing) {
        const payload: any = {
          name,
          name_ta: nameTa.trim() || null,
          voice_aliases: voiceAliases.trim() || null,
          category,
          pack_size_value: Number(packVal),
          pack_size_unit: packUnit,
          packets_per_carton: Number(packetsPerCarton),
          selling_price_paise: pricePaise,
          gst_rate_pct: Number(gstRate),
          hsn_code: hsnCode.trim(),
          shelf_life_days: Number(shelfLife),
          reorder_level_packets: Number(reorderPackets),
          is_active: isActive,
          expected_yield_packets: Number(expectedYield || 200),
          bom_items: bomItemsPayload,
        };
        if (effectiveFrom) payload.effective_from = new Date(effectiveFrom).toISOString();
        const res = await fetch(`/api/v1/products/${editing.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
          body: JSON.stringify(payload),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Update failed');
        setMsg({ text: `Updated product ${data.name}`, type: 'success' });
      } else {
        const payload: any = {
          name,
          name_ta: nameTa.trim() || null,
          voice_aliases: voiceAliases.trim() || null,
          code: code.trim() || undefined,
          category,
          pack_size_value: Number(packVal),
          pack_size_unit: packUnit,
          packets_per_carton: Number(packetsPerCarton),
          selling_price_paise: pricePaise,
          gst_rate_pct: Number(gstRate),
          hsn_code: hsnCode.trim(),
          shelf_life_days: Number(shelfLife),
          reorder_level_packets: Number(reorderPackets),
          is_active: isActive,
          expected_yield_packets: Number(expectedYield || 200),
          bom_items: bomItemsPayload.length > 0 ? bomItemsPayload : undefined,
        };
        if (openingPackets && Number(openingPackets) > 0) {
          payload.opening_stock_packets = Number(openingPackets);
          if (batchNo.trim()) payload.batch_no = batchNo.trim();
          if (expiryDate) payload.expiry_date = expiryDate;
        }
        const res = await fetch('/api/v1/products', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
          body: JSON.stringify(payload),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Create failed');
        setMsg({ text: `Created product ${data.name} (${data.code})`, type: 'success' });
      }
      setShowModal(false);
      loadAll();
    } catch (err: any) {
      setMsg({ text: err.message || 'Save failed', type: 'error' });
    }
  };

  const openDuplicate = (p: any) => {
    setDupSource(p);
    setDupName(`${p.name} 500g`);
    setDupNameTa(p.name_ta || '');
    setDupPackVal('500');
    setDupPackUnit('g');
    const ratio = 500 / Number(p.pack_size_g || 200);
    setDupPriceRs((((p.selling_price_paise || 5000) * ratio) / 100).toFixed(2));
    setDupOpening('');
  };

  const handleDuplicateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!dupSource) return;
    try {
      const payload: any = {
        name: dupName,
        name_ta: dupNameTa.trim() || undefined,
        pack_size_value: Number(dupPackVal),
        pack_size_unit: dupPackUnit,
        selling_price_paise: dupPriceRs ? Math.round(Number(dupPriceRs) * 100) : undefined,
        opening_stock_packets: dupOpening && Number(dupOpening) > 0 ? Number(dupOpening) : undefined,
      };
      const res = await fetch(`/api/v1/products/${dupSource.id}/duplicate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Duplicate failed');
      setMsg({ text: `Duplicated ${data.name} (${data.code}) with scaled BOM!`, type: 'success' });
      setDupSource(null);
      loadAll();
    } catch (err: any) {
      setMsg({ text: err.message || 'Duplicate failed', type: 'error' });
    }
  };

  const handleDeactivate = async (p: any) => {
    try {
      const res = await fetch(`/api/v1/products/${p.id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Action failed');
      setMsg({ text: data.message || `${p.name} updated.`, type: 'success' });
      loadAll();
    } catch (err: any) {
      setMsg({ text: err.message, type: 'error' });
    }
  };

  const filtered = products.filter((p) => {
    const q = search.trim().toLowerCase();
    if (!q) return true;
    return (
      p.name.toLowerCase().includes(q) ||
      (p.name_ta || '').toLowerCase().includes(q) ||
      p.code.toLowerCase().includes(q) ||
      (p.voice_aliases || '').toLowerCase().includes(q)
    );
  });

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

      <div className="flex flex-wrap gap-3 justify-between items-center bg-white dark:bg-stone-900 border border-stone-300 dark:border-stone-700 p-4 rounded">
        <div>
          <h3 className="text-sm font-bold text-stone-900 dark:text-white">Products & Recipe (BOM) Catalog</h3>
          <p className="text-xs text-stone-500">Add, edit, duplicate with BOM scaling, or deactivate products.</p>
        </div>
        <div className="flex gap-2 items-center">
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search English / Tamil / alias..."
            className="min-h-[38px] px-3 border border-stone-300 rounded text-xs bg-white dark:bg-stone-800"
          />
          <button
            onClick={openCreate}
            className="min-h-[38px] px-4 bg-leaf-600 hover:bg-leaf-700 text-white font-bold text-xs rounded"
          >
            + Add Product
          </button>
        </div>
      </div>

      <div className="bg-white dark:bg-stone-900 border border-stone-300 dark:border-stone-700 rounded overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead className="bg-stone-100 dark:bg-stone-800 border-b border-stone-200 font-bold">
            <tr>
              <th className="p-3">Code</th>
              <th className="p-3">Product (EN / தமிழ்)</th>
              <th className="p-3">Pack</th>
              <th className="p-3">Price</th>
              <th className="p-3">GST / HSN</th>
              <th className="p-3">Stock</th>
              <th className="p-3">Status</th>
              <th className="p-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-stone-200 dark:divide-stone-800">
            {filtered.map((p) => (
              <tr key={p.id} className="hover:bg-cream-50 dark:hover:bg-stone-800/50">
                <td className="p-3 font-mono font-semibold text-turmeric-700">{p.code}</td>
                <td className="p-3">
                  <div className="font-semibold">{p.name}</div>
                  {p.name_ta && <div className="text-[11px] text-stone-500">{p.name_ta}</div>}
                </td>
                <td className="p-3">{p.pack_size_value} {p.pack_size_unit}</td>
                <td className="p-3 font-bold">Rs {(p.selling_price_paise / 100).toFixed(2)}</td>
                <td className="p-3">{p.gst_rate_pct}% / {p.hsn_code}</td>
                <td className="p-3 font-semibold">{p.balance_packets} pkts</td>
                <td className="p-3">
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                      p.is_active ? 'bg-emerald-100 text-emerald-800' : 'bg-stone-200 text-stone-600'
                    }`}
                  >
                    {p.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td className="p-3 text-right space-x-1.5">
                  <button
                    onClick={() => openEdit(p)}
                    className="px-2 py-1 bg-stone-200 dark:bg-stone-700 font-semibold rounded hover:bg-stone-300"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => openDuplicate(p)}
                    className="px-2 py-1 bg-turmeric-600 text-white font-semibold rounded hover:bg-turmeric-700"
                  >
                    Duplicate
                  </button>
                  {p.is_active && (
                    <button
                      onClick={() => handleDeactivate(p)}
                      className="px-2 py-1 bg-rose-100 text-rose-700 font-semibold rounded hover:bg-rose-200"
                    >
                      Deactivate
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Add / Edit Product Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <form
            onSubmit={handleSaveProduct}
            className="bg-white dark:bg-stone-900 border border-stone-300 dark:border-stone-700 rounded max-w-2xl w-full p-5 space-y-4 max-h-[92vh] overflow-y-auto"
          >
            <h3 className="font-bold text-base text-stone-900 dark:text-white">
              {editing ? `Edit Product: ${editing.name}` : 'Add New Product & Recipe'}
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
              <div>
                <label className="block font-semibold mb-1">Product Name (EN) *</label>
                <input
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full min-h-[36px] px-2.5 border border-stone-300 rounded bg-white dark:bg-stone-800"
                />
              </div>
              <div>
                <label className="block font-semibold mb-1">Tamil Name (தமிழ்)</label>
                <input
                  value={nameTa}
                  onChange={(e) => setNameTa(e.target.value)}
                  className="w-full min-h-[36px] px-2.5 border border-stone-300 rounded bg-white dark:bg-stone-800"
                />
              </div>
              <div>
                <label className="block font-semibold mb-1">Code (blank = auto)</label>
                <input
                  value={code}
                  disabled={!!editing}
                  onChange={(e) => setCode(e.target.value)}
                  className="w-full min-h-[36px] px-2.5 border border-stone-300 rounded bg-white dark:bg-stone-800 disabled:opacity-60"
                />
              </div>
              <div>
                <label className="block font-semibold mb-1">Voice Aliases (comma-separated)</label>
                <input
                  value={voiceAliases}
                  onChange={(e) => setVoiceAliases(e.target.value)}
                  className="w-full min-h-[36px] px-2.5 border border-stone-300 rounded bg-white dark:bg-stone-800"
                  placeholder="murukku, kai murukku"
                />
              </div>
              <div>
                <label className="block font-semibold mb-1">Category</label>
                <input
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full min-h-[36px] px-2.5 border border-stone-300 rounded bg-white dark:bg-stone-800"
                />
              </div>
              <div className="grid grid-cols-2 gap-1.5">
                <div>
                  <label className="block font-semibold mb-1">Pack Size *</label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    value={packVal}
                    onChange={(e) => setPackVal(e.target.value)}
                    className="w-full min-h-[36px] px-2 border border-stone-300 rounded bg-white dark:bg-stone-800"
                  />
                </div>
                <div>
                  <label className="block font-semibold mb-1">Unit</label>
                  <select
                    value={packUnit}
                    onChange={(e) => setPackUnit(e.target.value)}
                    className="w-full min-h-[36px] px-2 border border-stone-300 rounded bg-white dark:bg-stone-800"
                  >
                    <option value="g">g</option>
                    <option value="kg">kg</option>
                    <option value="ml">ml</option>
                    <option value="l">l</option>
                    <option value="piece">piece</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="block font-semibold mb-1">Selling Price (Rs) *</label>
                <input
                  type="number"
                  step="0.01"
                  required
                  value={priceRs}
                  onChange={(e) => setPriceRs(e.target.value)}
                  className="w-full min-h-[36px] px-2.5 border border-stone-300 rounded bg-white dark:bg-stone-800"
                />
              </div>
              <div>
                <label className="block font-semibold mb-1">GST Rate %</label>
                <input
                  type="number"
                  step="0.01"
                  value={gstRate}
                  onChange={(e) => setGstRate(e.target.value)}
                  className="w-full min-h-[36px] px-2.5 border border-stone-300 rounded bg-white dark:bg-stone-800"
                />
              </div>
              <div>
                <label className="block font-semibold mb-1">HSN (4/6/8 digits)</label>
                <input
                  required
                  value={hsnCode}
                  onChange={(e) => setHsnCode(e.target.value)}
                  className="w-full min-h-[36px] px-2.5 border border-stone-300 rounded bg-white dark:bg-stone-800"
                />
              </div>
              <div>
                <label className="block font-semibold mb-1">Packets / Carton</label>
                <input
                  type="number"
                  value={packetsPerCarton}
                  onChange={(e) => setPacketsPerCarton(e.target.value)}
                  className="w-full min-h-[36px] px-2.5 border border-stone-300 rounded bg-white dark:bg-stone-800"
                />
              </div>
              <div>
                <label className="block font-semibold mb-1">Shelf Life (days)</label>
                <input
                  type="number"
                  value={shelfLife}
                  onChange={(e) => setShelfLife(e.target.value)}
                  className="w-full min-h-[36px] px-2.5 border border-stone-300 rounded bg-white dark:bg-stone-800"
                />
              </div>
              <div>
                <label className="block font-semibold mb-1">Reorder Level (pkts)</label>
                <input
                  type="number"
                  value={reorderPackets}
                  onChange={(e) => setReorderPackets(e.target.value)}
                  className="w-full min-h-[36px] px-2.5 border border-stone-300 rounded bg-white dark:bg-stone-800"
                />
              </div>
            </div>

            {editing && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs items-center">
                <div>
                  <label className="block font-semibold mb-1">Price/GST Effective Date (optional)</label>
                  <input
                    type="datetime-local"
                    value={effectiveFrom}
                    onChange={(e) => setEffectiveFrom(e.target.value)}
                    className="w-full min-h-[36px] px-2.5 border border-stone-300 rounded bg-white dark:bg-stone-800"
                  />
                </div>
                <label className="flex items-center gap-2 font-semibold pt-4">
                  <input type="checkbox" checked={isActive} onChange={(e) => setIsActive(e.target.checked)} />
                  Active Product
                </label>
              </div>
            )}

            {!editing && (
              <div className="border-t border-stone-200 pt-3 space-y-2 text-xs">
                <div className="font-bold text-stone-700 dark:text-stone-300">
                  Optional Opening Stock (posts to stock_ledger as opening_balance)
                </div>
                <div className="grid grid-cols-3 gap-2">
                  <div>
                    <label className="block font-semibold mb-1">Opening Packets</label>
                    <input
                      type="number"
                      min="0"
                      value={openingPackets}
                      onChange={(e) => setOpeningPackets(e.target.value)}
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

            {/* Recipe (BOM) Section */}
            <div className="border-t border-stone-200 pt-3 space-y-2 text-xs">
              <div className="flex justify-between items-center">
                <span className="font-bold text-stone-800 dark:text-stone-200">Recipe (BOM)</span>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => setShowInlineRm(!showInlineRm)}
                    className="px-2.5 py-1 border border-stone-300 rounded font-semibold hover:bg-stone-100"
                  >
                    + Inline New Raw Material
                  </button>
                  <button
                    type="button"
                    onClick={addBomRow}
                    className="px-2.5 py-1 bg-turmeric-600 text-white rounded font-semibold hover:bg-turmeric-700"
                  >
                    + Add Ingredient
                  </button>
                </div>
              </div>

              {showInlineRm && (
                <div className="p-2.5 bg-cream-50 dark:bg-stone-800 border border-stone-200 rounded flex flex-wrap gap-2 items-end">
                  <input
                    value={newRmName}
                    onChange={(e) => setNewRmName(e.target.value)}
                    placeholder="Material name"
                    className="min-h-[32px] px-2 border border-stone-300 rounded bg-white dark:bg-stone-900"
                  />
                  <select
                    value={newRmType}
                    onChange={(e) => setNewRmType(e.target.value as 'raw' | 'packaging')}
                    className="min-h-[32px] px-2 border border-stone-300 rounded bg-white dark:bg-stone-900"
                  >
                    <option value="raw">Raw</option>
                    <option value="packaging">Packaging</option>
                  </select>
                  <select
                    value={newRmUnit}
                    onChange={(e) => setNewRmUnit(e.target.value as 'g' | 'ml' | 'piece')}
                    className="min-h-[32px] px-2 border border-stone-300 rounded bg-white dark:bg-stone-900"
                  >
                    <option value="g">g</option>
                    <option value="ml">ml</option>
                    <option value="piece">piece</option>
                  </select>
                  <button
                    type="button"
                    onClick={handleInlineAddRm}
                    className="min-h-[32px] px-3 bg-leaf-600 text-white rounded font-bold"
                  >
                    Save & Add
                  </button>
                </div>
              )}

              <div className="w-48">
                <label className="block font-semibold mb-1">Expected Yield (packets/batch)</label>
                <input
                  type="number"
                  min="1"
                  value={expectedYield}
                  onChange={(e) => setExpectedYield(e.target.value)}
                  className="w-full min-h-[34px] px-2 border border-stone-300 rounded bg-white dark:bg-stone-800"
                />
              </div>

              {bomRows.map((row, idx) => {
                const selectedRm = materials.find((m) => m.id === Number(row.raw_material_id));
                return (
                  <div key={idx} className="flex gap-2 items-center">
                    <select
                      value={row.raw_material_id}
                      onChange={(e) => {
                        const copy = [...bomRows];
                        copy[idx].raw_material_id = Number(e.target.value);
                        setBomRows(copy);
                      }}
                      className="flex-1 min-h-[34px] px-2 border border-stone-300 rounded bg-white dark:bg-stone-800"
                    >
                      {materials.map((m) => (
                        <option key={m.id} value={m.id}>
                          {m.name} ({m.code}) [{m.base_unit}]
                        </option>
                      ))}
                    </select>
                    <input
                      type="number"
                      step="0.01"
                      value={row.standard_qty_base}
                      onChange={(e) => {
                        const copy = [...bomRows];
                        copy[idx].standard_qty_base = e.target.value;
                        setBomRows(copy);
                      }}
                      className="w-28 min-h-[34px] px-2 border border-stone-300 rounded bg-white dark:bg-stone-800"
                    />
                    <span className="w-10 text-stone-500">{selectedRm?.base_unit || ''}</span>
                    <button
                      type="button"
                      onClick={() => setBomRows(bomRows.filter((_, i) => i !== idx))}
                      className="px-2 py-1 text-rose-600 font-bold"
                    >
                      ✕
                    </button>
                  </div>
                );
              })}
            </div>

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
                {editing ? 'Save Product' : 'Create Product'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Duplicate Product Modal */}
      {dupSource && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <form
            onSubmit={handleDuplicateSubmit}
            className="bg-white dark:bg-stone-900 border border-stone-300 rounded max-w-md w-full p-5 space-y-3 text-xs"
          >
            <h3 className="font-bold text-base">Duplicate & Scale BOM from {dupSource.name}</h3>
            <p className="text-stone-500">
              Source pack: {dupSource.pack_size_value} {dupSource.pack_size_unit}. Raw material quantities will scale automatically by pack weight ratio.
            </p>
            <div>
              <label className="block font-semibold mb-1">New Product Name *</label>
              <input
                required
                value={dupName}
                onChange={(e) => setDupName(e.target.value)}
                className="w-full min-h-[36px] px-2.5 border border-stone-300 rounded bg-white dark:bg-stone-800"
              />
            </div>
            <div>
              <label className="block font-semibold mb-1">Tamil Name</label>
              <input
                value={dupNameTa}
                onChange={(e) => setDupNameTa(e.target.value)}
                className="w-full min-h-[36px] px-2.5 border border-stone-300 rounded bg-white dark:bg-stone-800"
              />
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block font-semibold mb-1">New Pack Size *</label>
                <input
                  type="number"
                  step="0.01"
                  required
                  value={dupPackVal}
                  onChange={(e) => setDupPackVal(e.target.value)}
                  className="w-full min-h-[36px] px-2.5 border border-stone-300 rounded bg-white dark:bg-stone-800"
                />
              </div>
              <div>
                <label className="block font-semibold mb-1">Unit</label>
                <select
                  value={dupPackUnit}
                  onChange={(e) => setDupPackUnit(e.target.value)}
                  className="w-full min-h-[36px] px-2.5 border border-stone-300 rounded bg-white dark:bg-stone-800"
                >
                  <option value="g">g</option>
                  <option value="kg">kg</option>
                  <option value="ml">ml</option>
                  <option value="l">l</option>
                </select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block font-semibold mb-1">Selling Price (Rs)</label>
                <input
                  type="number"
                  step="0.01"
                  value={dupPriceRs}
                  onChange={(e) => setDupPriceRs(e.target.value)}
                  className="w-full min-h-[36px] px-2.5 border border-stone-300 rounded bg-white dark:bg-stone-800"
                />
              </div>
              <div>
                <label className="block font-semibold mb-1">Opening Stock (pkts)</label>
                <input
                  type="number"
                  min="0"
                  value={dupOpening}
                  onChange={(e) => setDupOpening(e.target.value)}
                  className="w-full min-h-[36px] px-2.5 border border-stone-300 rounded bg-white dark:bg-stone-800"
                />
              </div>
            </div>
            <div className="flex gap-2 pt-2">
              <button
                type="button"
                onClick={() => setDupSource(null)}
                className="flex-1 min-h-[38px] border border-stone-300 rounded font-semibold"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="flex-1 min-h-[38px] bg-turmeric-600 text-white font-bold rounded"
              >
                Duplicate Product
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};
