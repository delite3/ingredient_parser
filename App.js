import { useState, useRef } from 'react';
import { StyleSheet, Text, View, Alert, TouchableOpacity, Linking, Platform } from 'react-native';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';
import { CameraView, useCameraPermissions } from 'expo-camera';

export default function App() {
  const [permission, requestPermission] = useCameraPermissions();
  const [scanned, setScanned] = useState(false);
  const [scanData, setScanData] = useState(null);
  const lastScanTime = useRef(0);
  const SCAN_COOLDOWN = 2000; // 2 seconds between scans

  // Handle barcode scan with cooldown
  const handleBarCodeScanned = ({ type, data }) => {
    const now = Date.now();
    
    // Prevent rapid repeated scans
    if (now - lastScanTime.current < SCAN_COOLDOWN) {
      return;
    }
    
    lastScanTime.current = now;
    setScanned(true);
    setScanData({ type, data });
    Alert.alert(
      'Barcode Scanned!',
      `Type: ${type}\nData: ${data}`,
      [{ text: 'OK', onPress: () => setScanned(false) }]
    );
  };

  // Handle permission request
  const handlePermissionRequest = async () => {
    const result = await requestPermission();
    
    // If permission was denied and can't ask again, guide user to settings
    if (!result.granted && result.canAskAgain === false) {
      Alert.alert(
        'Camera Permission Required',
        'Please enable camera access in your device settings to use the barcode scanner.',
        [
          { text: 'Cancel', style: 'cancel' },
          { 
            text: 'Open Settings', 
            onPress: () => {
              if (Platform.OS === 'ios') {
                Linking.openURL('app-settings:');
              } else {
                Linking.openSettings();
              }
            }
          }
        ]
      );
    }
  };

  // Show loading state while checking permissions
  if (!permission) {
    return (
      <SafeAreaProvider>
        <SafeAreaView style={styles.container} edges={['top', 'bottom']}>
          <View style={styles.centerContent}>
            <Text style={styles.text}>Checking camera permission...</Text>
          </View>
        </SafeAreaView>
      </SafeAreaProvider>
    );
  }

  // Show permission request if not granted
  if (!permission.granted) {
    return (
      <SafeAreaProvider>
        <SafeAreaView style={styles.container} edges={['top', 'bottom']}>
          <View style={styles.centerContent}>
            <Text style={styles.text}>📷 Camera Access Required</Text>
            <Text style={styles.subtext}>
              This app needs camera access to scan barcodes
            </Text>
            <TouchableOpacity 
              style={styles.button} 
              onPress={handlePermissionRequest}
            >
              <Text style={styles.buttonText}>Grant Permission</Text>
            </TouchableOpacity>
          </View>
        </SafeAreaView>
      </SafeAreaProvider>
    );
  }

  // Main scanner interface
  return (
    <SafeAreaProvider>
      <SafeAreaView style={styles.container} edges={['top', 'bottom']}>
      <View style={styles.header}>
        <Text style={styles.title}>Barcode Scanner</Text>
        <Text style={styles.subtitle}>Point camera at a barcode</Text>
      </View>

      <View style={styles.cameraContainer}>
        <CameraView
          onBarcodeScanned={scanned ? undefined : handleBarCodeScanned}
          barcodeScannerSettings={{
            barcodeTypes: ['qr', 'ean13', 'ean8', 'upc_a', 'upc_e', 'code128', 'code39', 'code93', 'codabar', 'itf14', 'pdf417', 'aztec', 'datamatrix'],
          }}
          style={StyleSheet.absoluteFillObject}
        />
        
        {/* Scanning frame overlay */}
        <View style={styles.scanFrame}>
          <View style={[styles.corner, styles.topLeft]} />
          <View style={[styles.corner, styles.topRight]} />
          <View style={[styles.corner, styles.bottomLeft]} />
          <View style={[styles.corner, styles.bottomRight]} />
        </View>
      </View>

      {/* Result display */}
      {scanData && (
        <View style={styles.resultContainer}>
          <Text style={styles.resultTitle}>Last Scanned:</Text>
          <Text style={styles.resultType}>Type: {scanData.type}</Text>
          <Text style={styles.resultData}>{scanData.data}</Text>
        </View>
      )}

      {/* Scan again button */}
      {scanned && (
        <TouchableOpacity 
          style={styles.button} 
          onPress={() => setScanned(false)}
        >
          <Text style={styles.buttonText}>Tap to Scan Again</Text>
        </TouchableOpacity>
      )}
      </SafeAreaView>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1a1a2e',
  },
  centerContent: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 40,
  },
  header: {
    padding: 20,
    alignItems: 'center',
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 5,
  },
  subtitle: {
    fontSize: 16,
    color: '#aaa',
  },
  cameraContainer: {
    flex: 1,
    margin: 20,
    borderRadius: 20,
    overflow: 'hidden',
    backgroundColor: '#000',
  },
  scanFrame: {
    position: 'absolute',
    top: '30%',
    left: '15%',
    right: '15%',
    height: '40%',
  },
  corner: {
    position: 'absolute',
    width: 40,
    height: 40,
    borderColor: '#00ff88',
    borderWidth: 4,
  },
  topLeft: {
    top: 0,
    left: 0,
    borderBottomWidth: 0,
    borderRightWidth: 0,
  },
  topRight: {
    top: 0,
    right: 0,
    borderBottomWidth: 0,
    borderLeftWidth: 0,
  },
  bottomLeft: {
    bottom: 0,
    left: 0,
    borderTopWidth: 0,
    borderRightWidth: 0,
  },
  bottomRight: {
    bottom: 0,
    right: 0,
    borderTopWidth: 0,
    borderLeftWidth: 0,
  },
  resultContainer: {
    backgroundColor: '#16213e',
    margin: 20,
    padding: 20,
    borderRadius: 15,
  },
  resultTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#00ff88',
    marginBottom: 10,
  },
  resultType: {
    fontSize: 14,
    color: '#aaa',
    marginBottom: 5,
  },
  resultData: {
    fontSize: 16,
    color: '#fff',
    fontWeight: '500',
  },
  button: {
    backgroundColor: '#00ff88',
    margin: 20,
    padding: 18,
    borderRadius: 15,
    alignItems: 'center',
  },
  buttonText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1a1a2e',
  },
  text: {
    fontSize: 22,
    color: '#fff',
    textAlign: 'center',
    marginBottom: 15,
    fontWeight: '600',
  },
  subtext: {
    fontSize: 16,
    color: '#aaa',
    textAlign: 'center',
    marginBottom: 30,
    lineHeight: 24,
  },
});
