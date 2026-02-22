/**
 * App.js — Root component.
 *
 * Thin shell that:
 *   1. Sets up the NavigationContainer
 *   2. Initialises the shared hooks (scan history + barcode scanner)
 *   3. Passes everything into the navigator
 *
 * All UI lives under  src/screens/ , all logic under  src/hooks/  and  src/services/ .
 */
import React from 'react';
import { View, Text, ActivityIndicator, StyleSheet } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { NavigationContainer } from '@react-navigation/native';

import AppNavigator from './src/navigation/AppNavigator';
import { useScanHistory } from './src/hooks/useScanHistory';
import { useBarcodeScanner } from './src/hooks/useBarcodeScanner';
import { COLORS } from './src/constants/theme';

export default function App() {
  const { scannedItems, addItem, removeLastItem, isLoaded } = useScanHistory();

  const {
    scanned,
    loading,
    countdown,
    processBarcode,
    cancelScan,
    markScanned,
    resetScanned,
  } = useBarcodeScanner({ addItem, removeLastItem });

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

  // Bundle everything the navigator needs into a single props object
  const scannerProps = {
    processBarcode,
    cancelScan,
    scanned,
    markScanned,
    resetScanned,
    countdown,
    loading,
    itemCount: scannedItems.length,
  };

  return (
    <SafeAreaProvider>
      <NavigationContainer>
        <AppNavigator scannerProps={scannerProps} scannedItems={scannedItems} />
      </NavigationContainer>
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
