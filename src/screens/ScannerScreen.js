/**
 * ScannerScreen — live camera view for barcode scanning.
 */
import React, { useCallback } from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';
import ScannerOverlay from '../components/ScannerOverlay';
import CountdownBanner from '../components/CountdownBanner';
import { COLORS, SPACING, FONT_SIZES, BORDER_RADIUS } from '../constants/theme';

export default function ScannerScreen({ navigation, route }) {
  const { processBarcode, cancelScan, scanned, markScanned, resetScanned, countdown, loading } =
    route.params ?? {};

  const [permission, requestPermission] = useCameraPermissions();

  const handleBarCodeScanned = useCallback(
    ({ type, data }) => {
      if (scanned || countdown > 0 || loading) return;
      markScanned();
      processBarcode(type, data, (item) => {
        navigation.navigate('Details', { item });
      });
    },
    [scanned, countdown, loading, markScanned, processBarcode, navigation],
  );

  const handleBack = useCallback(() => {
    resetScanned();
    navigation.goBack();
  }, [resetScanned, navigation]);

  // Permission not yet determined
  if (!permission) {
    return (
      <View style={styles.centerContent}>
        <Text style={styles.text}>Checking camera permission...</Text>
      </View>
    );
  }

  // Permission denied
  if (!permission.granted) {
    return (
      <View style={styles.centerContent}>
        <Text style={styles.text}>📷 Camera Access Required</Text>
        <Text style={styles.subtext}>
          This app needs camera access to scan barcodes
        </Text>
        <TouchableOpacity style={styles.button} onPress={requestPermission}>
          <Text style={styles.buttonText}>Grant Permission</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.backButton} onPress={handleBack}>
          <Text style={styles.backButtonText}>← Back</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={handleBack}>
          <Text style={styles.backLink}>← Back</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Scan Barcode</Text>
        <View style={{ width: 50 }} />
      </View>

      <View style={styles.cameraContainer}>
        <CameraView
          onBarcodeScanned={scanned ? undefined : handleBarCodeScanned}
          barcodeScannerSettings={{
            barcodeTypes: [
              'qr', 'ean13', 'ean8', 'upc_a', 'upc_e',
              'code128', 'code39', 'code93', 'codabar',
              'itf14', 'pdf417', 'aztec', 'datamatrix',
            ],
          }}
          style={StyleSheet.absoluteFillObject}
        />
        <ScannerOverlay />
      </View>

      {countdown > 0 && (
        <CountdownBanner seconds={countdown} onUndo={cancelScan} />
      )}

      {!scanned && countdown === 0 && (
        <View style={styles.instructionBox}>
          <Text style={styles.instructionText}>Point camera at barcode</Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  centerContent: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: SPACING.xxl,
    backgroundColor: COLORS.background,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: SPACING.xl,
    paddingBottom: 10,
  },
  headerTitle: {
    fontSize: FONT_SIZES.xxl,
    fontWeight: 'bold',
    color: COLORS.textPrimary,
  },
  backLink: {
    fontSize: FONT_SIZES.xl,
    color: COLORS.primary,
    fontWeight: '600',
  },
  cameraContainer: {
    flex: 1,
    margin: SPACING.xl,
    borderRadius: BORDER_RADIUS.xxl,
    overflow: 'hidden',
    backgroundColor: COLORS.black,
  },
  instructionBox: {
    backgroundColor: 'rgba(0, 255, 136, 0.2)',
    margin: SPACING.xl,
    padding: SPACING.lg,
    borderRadius: BORDER_RADIUS.lg,
    borderWidth: 1,
    borderColor: COLORS.primary,
  },
  instructionText: {
    fontSize: FONT_SIZES.lg,
    color: COLORS.primary,
    textAlign: 'center',
    fontWeight: '600',
  },
  text: {
    fontSize: 22,
    color: COLORS.textPrimary,
    textAlign: 'center',
    marginBottom: SPACING.lg,
    fontWeight: '600',
  },
  subtext: {
    fontSize: FONT_SIZES.lg,
    color: COLORS.textSecondary,
    textAlign: 'center',
    marginBottom: SPACING.xxl,
    lineHeight: 24,
  },
  button: {
    backgroundColor: COLORS.primary,
    width: '100%',
    padding: SPACING.xl,
    borderRadius: BORDER_RADIUS.xl,
    alignItems: 'center',
    marginTop: 10,
  },
  buttonText: {
    fontSize: FONT_SIZES.xl,
    fontWeight: 'bold',
    color: COLORS.background,
  },
  backButton: {
    backgroundColor: COLORS.transparent,
    borderWidth: 2,
    borderColor: COLORS.primary,
    marginTop: SPACING.xl,
    padding: SPACING.lg,
    borderRadius: BORDER_RADIUS.lg,
    width: '100%',
    alignItems: 'center',
  },
  backButtonText: {
    fontSize: FONT_SIZES.lg,
    fontWeight: '600',
    color: COLORS.primary,
  },
});
