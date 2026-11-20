/**
 * IndexedDB Offline Queue for Salesman field orders.
 * Automatically buffers orders when offline and syncs when reconnected.
 */
const DB_NAME = 'SriLakshmiSnacksERP';
const STORE_NAME = 'offline_orders';
const DB_VERSION = 1;

function openDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME, { keyPath: 'id', autoIncrement: true });
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

export async function queueOfflineOrder(orderData: any): Promise<number> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readwrite');
    const store = tx.objectStore(STORE_NAME);
    const req = store.add({
      ...orderData,
      queued_at: new Date().toISOString()
    });
    req.onsuccess = () => resolve(req.result as number);
    req.onerror = () => reject(req.error);
  });
}

export async function getQueuedOrders(): Promise<any[]> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readonly');
    const store = tx.objectStore(STORE_NAME);
    const req = store.getAll();
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

export async function clearQueuedOrder(id: number): Promise<void> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readwrite');
    const store = tx.objectStore(STORE_NAME);
    const req = store.delete(id);
    req.onsuccess = () => resolve();
    req.onerror = () => reject(req.error);
  });
}

export async function syncOfflineOrders(
  submitFn: (order: any) => Promise<any>,
  onProgress?: (syncedCount: number) => void
): Promise<number> {
  const queued = await getQueuedOrders();
  let count = 0;
  for (const item of queued) {
    try {
      const { id, queued_at, ...cleanOrder } = item;
      await submitFn(cleanOrder);
      await clearQueuedOrder(id);
      count++;
      if (onProgress) onProgress(count);
    } catch (err) {
      console.error('Failed to sync queued order:', err);
      break; // stop on network failure
    }
  }
  return count;
}
