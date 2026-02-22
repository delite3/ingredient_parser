/**
 * useScanHistory — manages the scanned-items list with AsyncStorage persistence.
 *
 * Exposes:
 *   scannedItems    — the current list
 *   addItem         — append a new scan result (persists automatically)
 *   removeLastItem  — remove the most recent item (used by undo)
 *   isLoaded        — true once history has been read from disk
 */
import { useState, useEffect, useCallback } from 'react';
import { loadHistory, saveHistory } from '../services/storage';

export function useScanHistory() {
  const [scannedItems, setScannedItems] = useState([]);
  const [isLoaded, setIsLoaded] = useState(false);

  // Load persisted history on mount
  useEffect(() => {
    (async () => {
      const saved = await loadHistory();
      setScannedItems(saved);
      setIsLoaded(true);
    })();
  }, []);

  // Persist whenever the list changes (but only after initial load)
  useEffect(() => {
    if (isLoaded) {
      saveHistory(scannedItems);
    }
  }, [scannedItems, isLoaded]);

  const addItem = useCallback((item) => {
    setScannedItems((prev) => [item, ...prev]);
  }, []);

  const removeLastItem = useCallback(() => {
    setScannedItems((prev) => prev.slice(1));
  }, []);

  return { scannedItems, addItem, removeLastItem, isLoaded };
}
