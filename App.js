/**
 * App.js — Root component.
 *
 * Thin shell that:
 *   1. Sets up the NavigationContainer
 *   2. Initialises the shared hooks (scan history + barcode scanner)
 *   3. Wraps everything in Context providers so screens access state directly
 *
 * All UI lives under  src/screens/ , all logic under  src/hooks/  and  src/services/ .
 */
import React, { useMemo } from 'react';
import { View, Text, ActivityIndicator, StyleSheet } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { NavigationContainer } from '@react-navigation/native';

import AppNavigator from './src/navigation/AppNavigator';
import { useScanHistory } from './src/hooks/useScanHistory';
import { useBarcodeScanner } from './src/hooks/useBarcodeScanner';
import { ScannerProvider } from './src/context/ScannerContext';
import { HistoryProvider } from './src/context/HistoryContext';
import { COLORS } from './src/constants/theme';

export default function App() {
  const { scannedItems, addItem, removeLastItem, removeItem, isLoaded } = useScanHistory();

  const {
    scanned,
    loading,
    countdown,
    processBarcode,
    cancelScan,
    markScanned,
    resetScanned,
  } = useBarcodeScanner({ addItem, removeLastItem });

  // Memoised context values — must be called before any early return (Rules of Hooks)
  const scannerValue = useMemo(
    () => ({
      processBarcode,
      cancelScan,
      scanned,
      markScanned,
      resetScanned,
      countdown,
      loading,
      itemCount: scannedItems.length,
    }),
    [processBarcode, cancelScan, scanned, markScanned, resetScanned, countdown, loading, scannedItems.length],
  );

  const historyValue = useMemo(
    () => ({ scannedItems, removeItem }),
    [scannedItems, removeItem],
  );

  // Wait for persisted history to load before rendering
  if (!isLoaded) {
    return (
      <SafeAreaProvider>
        <View style={styles.splash}>
          <ActivityIndicator size="large" color={COLORS.primary} />
          <Text style={styles.splashText}>Loading…</Text>
        </View>
      </SafeAreaProvider>
    );
  }

  return (
    <SafeAreaProvider>
      <HistoryProvider value={historyValue}>
        <ScannerProvider value={scannerValue}>
          <NavigationContainer>
            <AppNavigator />
          </NavigationContainer>
        </ScannerProvider>
      </HistoryProvider>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  splash: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: COLORS.background,
  },
  splashText: {
    marginTop: 12,
    fontSize: 16,
    color: COLORS.textSecondary,
  },
});
