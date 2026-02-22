/**
 * HistoryContext — shares scanned-items list with all screens via context.
 */
import React, { createContext, useContext } from 'react';

const HistoryContext = createContext(null);

export function HistoryProvider({ value, children }) {
  return (
    <HistoryContext.Provider value={value}>
      {children}
    </HistoryContext.Provider>
  );
}

export function useHistory() {
  const ctx = useContext(HistoryContext);
  if (!ctx) {
    throw new Error('useHistory must be used within a HistoryProvider');
  }
  return ctx;
}
