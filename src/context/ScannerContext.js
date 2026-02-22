/**
 * ScannerContext — shares barcode-scanner state with all screens via context,
 * eliminating the need for inline render functions in navigators.
 */
import React, { createContext, useContext } from 'react';

const ScannerContext = createContext(null);

export function ScannerProvider({ value, children }) {
  return (
    <ScannerContext.Provider value={value}>
      {children}
    </ScannerContext.Provider>
  );
}

export function useScanner() {
  const ctx = useContext(ScannerContext);
  if (!ctx) {
    throw new Error('useScanner must be used within a ScannerProvider');
  }
  return ctx;
}
