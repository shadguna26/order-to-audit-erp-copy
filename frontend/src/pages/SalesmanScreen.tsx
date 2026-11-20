import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { startSpeechRecognition, ParsedVoiceOrder } from '../utils/speech';
import { queueOfflineOrder, syncOfflineOrders, getQueuedOrders } from '../utils/offlineQueue';

export const SalesmanScreen: React.FC<{ token: string; user: any; onSelectStock: (type: string, id: number) => void }> = ({ token, user, onSelectStock }) => {
  const { t, i18n } = useTranslation();
  const [customers, setCustomers] = useState<any[]>([]);
  const [products, setProducts] = useState<any[]>([]);
  const [selectedCustomerId, setSelectedCustomerId] = useState<number>(1);
  const [selectedProductId, setSelectedProductId] = useState<number>(1);
  const [quantity, setQuantity] = useState<number>(150);
  const [myOrders, setMyOrders] = useState<any[]>([]);

  const [stockCheck, setStockCheck] = useState<any>(null);
  const [isListening, setIsListening] = useState(false);
  const [voiceParsed, setVoiceParsed] = useState<ParsedVoiceOrder | null>(null);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [offlineCount, setOfflineCount] = useState(0);
  const [msg, setMsg] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  useEffect(() => {
    loadMasterData();
    loadMyOrders();
    updateOfflineStatus();

    const handleOnline = async () => {
      const count = await syncOfflineOrders(submitOrderDirect);
      if (count > 0) {
        setMsg({ text: `Synced ${count} offline orders successfully!`, type: 'success' });
        loadMyOrders();
      }
      updateOfflineStatus();
    };

    window.addEventListener('online', handleOnline);
    return () => window.removeEventListener('online', handleOnline);
  }, []);

  useEffect(() => {
    if (selectedProductId && quantity > 0) {
      checkLiveStock(selectedProductId, quantity);
    }
  }, [selectedProductId, quantity]);

  const updateOfflineStatus = async () => {
    const queued = await getQueuedOrders();
    setOfflineCount(queued.length);
  };

  const loadMasterData = async () => {
    try {
      const stockRes = await fetch('/api/v1/stock/summary', { headers: { Authorization: `Bearer ${token}` } });
      if (stockRes.ok) {
        const data = await stockRes.json();
        setProducts(data.finished_goods);
      }
      // Seeded customers
      setCustomers([
        { id: 1, name: 'Retailer A (Sri Balaji Provision Stores)', state: 'Tamil Nadu' },
        { id: 2, name: 'Distributor B (Cauvery Sweets & Snacks)', state: 'Karnataka' },
        { id: 3, name: 'Retailer C (Murugan Maligai)', state: 'Tamil Nadu' },
      ]);
    } catch {}
  };

  const loadMyOrders = async () => {
    try {
      const res = await fetch('/api/v1/orders', { headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) {
        setMyOrders(await res.json());
      }
    } catch {}
  };

  const checkLiveStock = async (prodId: number, qty: number) => {
    try {
      const res = await fetch(`/api/v1/orders/check-stock/${prodId}?quantity=${qty}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        setStockCheck(await res.json());
      }
    } catch {}
  };

  const submitOrderDirect = async (orderPayload: any) => {
    const res = await fetch('/api/v1/orders', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify(orderPayload)
    });
    if (!res.ok) throw new Error('Order creation failed');
    return res.json();
  };

  const handleOrderSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const orderPayload = {
      customer_id: selectedCustomerId,
      items: [{ product_id: selectedProductId, quantity_packets: quantity }]
    };

    if (!navigator.onLine) {
      await queueOfflineOrder(orderPayload);
      setMsg({ text: 'Order saved offline in local queue. Will sync when online.', type: 'success' });
      updateOfflineStatus();
      return;
    }

    try {
      await submitOrderDirect(orderPayload);
      setMsg({ text: 'Order submitted successfully!', type: 'success' });
      loadMyOrders();
      checkLiveStock(selectedProductId, quantity);
    } catch (err: any) {
      setMsg({ text: err.message || 'Failed to submit order', type: 'error' });
    }
  };

  const handleVoiceStart = () => {
    setIsListening(true);
    const speechLang = i18n.language === 'ta' ? 'ta-IN' : 'en-IN';
    startSpeechRecognition(
      speechLang,
      (parsed) => {
        setIsListening(false);
        setVoiceParsed(parsed);
        // Map parsed fields to selection if found
        if (parsed.matchedCustomerName) {
          const cust = customers.find((c) => c.name.includes(parsed.matchedCustomerName!));
          if (cust) setSelectedCustomerId(cust.id);
        }
        if (parsed.matchedProductName) {
          const prod = products.find((p) => p.name.includes(parsed.matchedProductName!));
          if (prod) setSelectedProductId(prod.id);
        }
        if (parsed.matchedQuantity) {
          setQuantity(parsed.matchedQuantity);
        }
        setShowConfirmModal(true);
      },
      (err) => {
        setIsListening(false);
        setMsg({ text: `Voice: ${err}`, type: 'error' });
      }
    );
  };

  return (
    <div className="max-w-2xl mx-auto space-y-5 pb-10">
      {/* Authentic Market Showcase Banner */}
      <div className="relative overflow-hidden rounded-xl border border-stone-300 dark:border-stone-700 bg-stone-900 text-white shadow-sm">
        <img
          src="/images/snacks_showcase.jpg"
          alt="Sri Lakshmi Snacks Traditional Display"
          className="w-full h-36 sm:h-44 object-cover object-center opacity-65"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/40 to-transparent flex flex-col justify-end p-4 sm:p-5">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] bg-turmeric-600 text-white font-bold px-2 py-0.5 rounded uppercase">
              Tiruchirappalli Fresh
            </span>
            <span className="text-xs text-amber-200 font-bold">
              Kai Murukku • Mixture • Thattai
            </span>
          </div>
          <p className="text-[11px] text-stone-300">
            Direct factory dispatch to retail stores across Tamil Nadu & South India
          </p>
        </div>
      </div>

      {offlineCount > 0 && (
        <div className="p-3 bg-amber-500 text-white font-medium text-xs rounded flex justify-between items-center">
          <span>{offlineCount} order(s) buffered offline.</span>
          <button onClick={() => syncOfflineOrders(submitOrderDirect)} className="underline font-bold">
            Sync Now
          </button>
        </div>
      )}

      {msg && (
        <div className={`p-3 rounded text-sm ${msg.type === 'success' ? 'bg-emerald-50 text-emerald-800 border border-emerald-300' : 'bg-rose-50 text-rose-800 border border-rose-300'}`}>
          {msg.text}
        </div>
      )}

      {/* Main Order Taking Pad */}
      <div className="bg-white dark:bg-stone-900 border border-stone-300 dark:border-stone-700 rounded p-5 shadow-sm">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-base font-bold text-stone-900 dark:text-white">
            {t('salesman.title')}
          </h2>
          <button
            type="button"
            onClick={handleVoiceStart}
            className={`min-h-[48px] px-4 rounded font-bold text-xs flex items-center gap-2 transition-all ${
              isListening ? 'bg-chilli-600 text-white animate-pulse' : 'bg-turmeric-100 text-turmeric-800 border border-turmeric-500 hover:bg-turmeric-200'
            }`}
          >
            <span>🎙️</span>
            {isListening ? t('salesman.listening') : t('salesman.voice_input')}
          </button>
        </div>

        <form onSubmit={handleOrderSubmit} className="space-y-4">
          {/* Customer Selection */}
          <div>
            <label className="block text-xs font-semibold text-stone-700 dark:text-stone-300 mb-1">
              {t('salesman.select_customer')}
            </label>
            <select
              value={selectedCustomerId}
              onChange={(e) => setSelectedCustomerId(Number(e.target.value))}
              className="w-full min-h-[48px] px-3 bg-white dark:bg-stone-800 border border-stone-300 dark:border-stone-700 rounded text-stone-900 dark:text-white text-sm"
            >
              {customers.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} ({c.state})
                </option>
              ))}
            </select>
          </div>

          {/* Product Selection */}
          <div>
            <label className="block text-xs font-semibold text-stone-700 dark:text-stone-300 mb-1">
              {t('salesman.add_products')}
            </label>
            <div className="grid grid-cols-2 gap-2 mb-2">
              {products.map((p) => {
                const isSelected = selectedProductId === p.id;
                return (
                  <button
                    key={p.id}
                    type="button"
                    onClick={() => setSelectedProductId(p.id)}
                    className={`p-2.5 rounded-lg border text-left transition flex flex-col justify-between ${
                      isSelected
                        ? 'border-turmeric-600 bg-amber-50 dark:bg-amber-950/40 shadow-xs'
                        : 'border-stone-200 dark:border-stone-700 bg-stone-50 dark:bg-stone-800 hover:border-turmeric-400'
                    }`}
                  >
                    <span className="font-bold text-xs text-stone-900 dark:text-white">{p.name}</span>
                    <span className="text-[11px] text-stone-500 font-mono mt-1">Stock: {p.balance_packets} pkts</span>
                  </button>
                );
              })}
            </div>
            <select
              value={selectedProductId}
              onChange={(e) => setSelectedProductId(Number(e.target.value))}
              className="w-full min-h-[44px] px-3 bg-white dark:bg-stone-800 border border-stone-300 dark:border-stone-700 rounded text-stone-900 dark:text-white text-xs"
            >
              {products.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} (Stock: {p.balance_packets} pkts)
                </option>
              ))}
            </select>
          </div>

          {/* Quantity Selector with Big Buttons */}
          <div>
            <label className="block text-xs font-semibold text-stone-700 dark:text-stone-300 mb-1">
              {t('common.quantity')} ({t('salesman.packets')})
            </label>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setQuantity((q) => Math.max(10, q - 10))}
                className="min-h-[48px] min-w-[48px] bg-stone-200 dark:bg-stone-700 font-bold rounded text-lg"
              >
                -10
              </button>
              <input
                type="number"
                value={quantity}
                onChange={(e) => setQuantity(Number(e.target.value))}
                className="flex-1 min-h-[48px] px-3 text-center text-lg font-bold border border-stone-300 dark:border-stone-700 rounded bg-white dark:bg-stone-800 text-stone-900 dark:text-white"
                required
              />
              <button
                type="button"
                onClick={() => setQuantity((q) => q + 10)}
                className="min-h-[48px] min-w-[48px] bg-stone-200 dark:bg-stone-700 font-bold rounded text-lg"
              >
                +10
              </button>
            </div>
          </div>

          {/* Live Stock Warning Alert */}
          {stockCheck && stockCheck.has_shortage && (
            <div className="p-3 bg-amber-50 border border-amber-300 rounded text-xs text-amber-900">
              <span className="font-bold block mb-1">⚠️ {t('salesman.stock_shortage')}</span>
              <p>{stockCheck.shortage_message}</p>
              <p className="mt-1 font-semibold text-stone-700">
                Suggested batches to produce: {stockCheck.suggested_batches_to_produce} batch(es)
              </p>
            </div>
          )}

          <button
            type="submit"
            className="w-full min-h-[52px] bg-turmeric-600 hover:bg-turmeric-700 text-white font-bold rounded text-base transition-colors shadow-sm"
          >
            {t('salesman.submit_order')}
          </button>
        </form>
      </div>

      {/* Voice Confirmation Dialog */}
      {showConfirmModal && voiceParsed && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-stone-900 border border-stone-300 rounded max-w-md w-full p-6 space-y-4">
            <h3 className="font-bold text-base text-stone-900 dark:text-white">
              {t('salesman.confirm_title')}
            </h3>
            <p className="text-xs text-stone-500 italic">"{voiceParsed.rawTranscript}"</p>

            <div className="text-xs space-y-2 border-y border-stone-200 py-3">
              <div>
                <span className="text-stone-500 block">Customer:</span>
                <span className="font-semibold text-stone-900 dark:text-white">
                  {customers.find((c) => c.id === selectedCustomerId)?.name}
                </span>
              </div>
              <div>
                <span className="text-stone-500 block">Product:</span>
                <span className="font-semibold text-stone-900 dark:text-white">
                  {products.find((p) => p.id === selectedProductId)?.name}
                </span>
              </div>
              <div>
                <span className="text-stone-500 block">Quantity:</span>
                <span className="font-semibold text-stone-900 dark:text-white text-base">
                  {quantity} packets
                </span>
              </div>
            </div>

            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setShowConfirmModal(false)}
                className="flex-1 min-h-[48px] border border-stone-300 rounded font-medium text-xs"
              >
                Cancel / Edit
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowConfirmModal(false);
                  handleOrderSubmit();
                }}
                className="flex-1 min-h-[48px] bg-leaf-600 text-white font-bold rounded text-xs"
              >
                Confirm & Submit
              </button>
            </div>
          </div>
        </div>
      )}

      {/* My Submitted Orders List */}
      <div className="bg-white dark:bg-stone-900 border border-stone-300 dark:border-stone-700 rounded p-5 shadow-sm">
        <h3 className="text-sm font-bold text-stone-900 dark:text-white mb-3">
          {t('salesman.my_orders')}
        </h3>
        <div className="divide-y divide-stone-200 dark:divide-stone-800 text-xs">
          {myOrders.length === 0 ? (
            <p className="text-stone-500 py-3">No orders yet.</p>
          ) : (
            myOrders.map((o) => (
              <div key={o.id} className="py-2.5 flex justify-between items-center">
                <div>
                  <span className="font-bold text-stone-900 dark:text-white">{o.order_no}</span>
                  <span className="text-stone-500 ml-2">Customer #{o.customer_id}</span>
                </div>
                <span className={`px-2 py-0.5 rounded uppercase font-semibold text-[10px] ${
                  o.status === 'dispatched' ? 'bg-emerald-100 text-emerald-800' :
                  o.status === 'invoiced' ? 'bg-blue-100 text-blue-800' :
                  o.status === 'approved' ? 'bg-amber-100 text-amber-800' : 'bg-stone-100 text-stone-700'
                }`}>
                  {o.status}
                </span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
