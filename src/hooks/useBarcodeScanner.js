/**
 * useBarcodeScanner — manages the scan + lookup + countdown lifecycle.
 *
 * Encapsulates the logic that was scattered across the old App component:
 *   – call lookupProduct
 *   – add the item to history
 *   – drive the 3-second countdown
 *   – support undo / cancel
 *
 * Returns everything the UI screens need to drive scanning.
 */
import { useState, useEffect, useRef, useCallback } from 'react';
import { lookupProduct } from '../services/openFoodFacts';

export function useBarcodeScanner({ addItem, removeLastItem }) {
  const [scanned, setScanned] = useState(false);
  const [loading, setLoading] = useState(false);
  const [countdown, setCountdown] = useState(0);
  const [latestItem, setLatestItem] = useState(null);
  const navigateOnComplete = useRef(null);

  // Drive the countdown timer
  useEffect(() => {
    if (countdown <= 0) return;
    const timer = setTimeout(() => {
      if (countdown === 1) {
        setCountdown(0);
        setScanned(false);
        // The caller will handle navigation via the returned onCountdownEnd callback
        if (navigateOnComplete.current) {
          navigateOnComplete.current(latestItem);
          navigateOnComplete.current = null;
        }
      } else {
        setCountdown((c) => c - 1);
      }
    }, 1000);
    return () => clearTimeout(timer);
  }, [countdown, latestItem]);

  /**
   * Process a barcode — look it up and start the countdown.
   * @param {string} type     – 'ean13', 'manual', 'test', etc.
   * @param {string} data     – the raw barcode value
   * @param {function} onDone – called when countdown finishes, receives the item
   */
  const processBarcode = useCallback(
    async (type, data, onDone) => {
      if (loading || countdown > 0) return;

      setLoading(true);
      const productInfo = await lookupProduct(data);

      const newItem = {
        id: Date.now().toString(),
        type,
        data,
        timestamp: new Date().toLocaleString(),
        product: productInfo,
      };

      addItem(newItem);
      setLatestItem(newItem);
      setLoading(false);
      navigateOnComplete.current = onDone;
      setCountdown(3);
    },
    [addItem, loading, countdown],
  );

  /** Cancel the countdown and undo the last scan. */
  const cancelScan = useCallback(() => {
    setCountdown(0);
    setScanned(false);
    setLatestItem(null);
    navigateOnComplete.current = null;
    removeLastItem();
  }, [removeLastItem]);

  /** Mark the scanner as having seen a barcode (dedup guard). */
  const markScanned = useCallback(() => setScanned(true), []);

  /** Reset the scanned flag (e.g. when the scanner screen re-focuses). */
  const resetScanned = useCallback(() => setScanned(false), []);

  return {
    scanned,
    loading,
    countdown,
    latestItem,
    processBarcode,
    cancelScan,
    markScanned,
    resetScanned,
  };
}
