import { useState } from 'react';
import { StyleSheet, Text, View, TouchableOpacity, TextInput, ScrollView, FlatList, ActivityIndicator, Image, Linking } from 'react-native';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';
import { CameraView, useCameraPermissions } from 'expo-camera';

export default function App() {
  const [permission, requestPermission] = useCameraPermissions();
  const [screen, setScreen] = useState('home'); // 'home', 'scanner', 'manual'
  const [scannedItems, setScannedItems] = useState([]);
  const [manualInput, setManualInput] = useState('');
  const [scanned, setScanned] = useState(false);
  const [loading, setLoading] = useState(false);

  // Lookup product information from APIs
  const lookupProduct = async (barcode) => {
    try {
      // Try Open Food Facts first (great for food products)
      const offResponse = await fetch(`https://world.openfoodfacts.org/api/v0/product/${barcode}.json`);
      const offData = await offResponse.json();
      
      if (offData.status === 1 && offData.product) {
        return {
          name: offData.product.product_name || 'Unknown Product',
          brand: offData.product.brands || '',
          image: offData.product.image_url || offData.product.image_front_url || null,
          source: 'Open Food Facts',
        };
      }
      
      // Fallback: could add more APIs here
      return null;
    } catch (error) {
      console.log('Lookup error:', error);
      return null;
    }
  };

  // Add barcode to history with product lookup
  const addBarcode = async (type, data) => {
    setLoading(true);
    
    // Lookup product info
    const productInfo = await lookupProduct(data);
    
    const newItem = {
      id: Date.now().toString(),
      type: type,
      data: data,
      timestamp: new Date().toLocaleString(),
      product: productInfo,
    };
    
    setScannedItems([newItem, ...scannedItems]);
    setLoading(false);
  };

  // Handle barcode scan (no cooldown, no alert)
  const handleBarCodeScanned = ({ type, data }) => {
    if (scanned) return;
    
    setScanned(true);
    addBarcode(type, data);
  };

  // Handle manual entry submission
  const handleManualSubmit = () => {
    if (manualInput.trim()) {
      addBarcode('manual', manualInput.trim());
      setManualInput('');
      setScreen('home');
    }
  };

  // Render Home Screen
  const renderHomeScreen = () => (
    <View style={styles.centerContent}>
      <Text style={styles.title}>🔍 Barcode Scanner</Text>
      <Text style={styles.subtitle}>Choose an option</Text>

      <TouchableOpacity 
        style={styles.primaryButton} 
        onPress={() => setScreen('scanner')}
      >
        <Text style={styles.primaryButtonIcon}>📷</Text>
        <Text style={styles.primaryButtonText}>Scan Barcode</Text>
      </TouchableOpacity>

      <TouchableOpacity 
        style={styles.secondaryButton} 
        onPress={() => setScreen('manual')}
      >
        <Text style={styles.secondaryButtonIcon}>✏️</Text>
        <Text style={styles.secondaryButtonText}>Enter Manually</Text>
      </TouchableOpacity>

      {/* Loading Indicator */}
      {loading && (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#00ff88" />
          <Text style={styles.loadingText}>Looking up product...</Text>
        </View>
      )}

      {/* Last Scanned List */}
      {scannedItems.length > 0 && (
        <View style={styles.historyContainer}>
          <Text style={styles.historyTitle}>Last Scanned ({scannedItems.length})</Text>
          <FlatList
            data={scannedItems}
            keyExtractor={(item) => item.id}
            renderItem={({ item }) => (
              <TouchableOpacity 
                style={styles.historyItem}
                onPress={() => item.data && Linking.openURL(`https://go-upc.com/search?q=${item.data}`)}
              >
                <View style={styles.historyItemContent}>
                  {item.product?.image && (
                    <Image 
                      source={{ uri: item.product.image }} 
                      style={styles.productImage}
                      resizeMode="cover"
                    />
                  )}
                  <View style={styles.historyItemText}>
                    <View style={styles.historyItemHeader}>
                      <Text style={styles.historyType}>{item.type.toUpperCase()}</Text>
                      <Text style={styles.historyTime}>{item.timestamp}</Text>
                    </View>
                    
                    {item.product ? (
                      <>
                        <Text style={styles.productName}>{item.product.name}</Text>
                        {item.product.brand && (
                          <Text style={styles.productBrand}>{item.product.brand}</Text>
                        )}
                        <Text style={styles.historyData}>{item.data}</Text>
                        <Text style={styles.productSource}>Source: {item.product.source}</Text>
                      </>
                    ) : (
                      <>
                        <Text style={styles.historyData}>{item.data}</Text>
                        <Text style={styles.noProductInfo}>No product info found</Text>
                      </>
                    )}
                  </View>
                </View>
                <Text style={styles.tapHint}>Tap to view on go-upc.com</Text>
              </TouchableOpacity>
            )}
          />
        </View>
      )}
    </View>
  );

  // Render Scanner Screen
  const renderScannerScreen = () => {
    if (!permission?.granted) {
      return (
        <View style={styles.centerContent}>
          <Text style={styles.text}>📷 Camera Access Required</Text>
          <Text style={styles.subtext}>
            This app needs camera access to scan barcodes
          </Text>
          <TouchableOpacity 
            style={styles.button} 
            onPress={requestPermission}
          >
            <Text style={styles.buttonText}>Grant Permission</Text>
          </TouchableOpacity>
          <TouchableOpacity 
            style={styles.backButton} 
            onPress={() => setScreen('home')}
          >
            <Text style={styles.backButtonText}>← Back</Text>
          </TouchableOpacity>
        </View>
      );
    }

    return (
      <>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => { setScreen('home'); setScanned(false); }}>
            <Text style={styles.backLink}>← Back</Text>
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Scan Barcode</Text>
          <View style={{ width: 50 }} />
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

        {/* Scan again button */}
        {scanned && (
          <TouchableOpacity 
            style={styles.button} 
            onPress={() => setScanned(false)}
          >
            <Text style={styles.buttonText}>✓ Scanned! Tap to Scan Again</Text>
          </TouchableOpacity>
        )}

        {!scanned && (
          <View style={styles.instructionBox}>
            <Text style={styles.instructionText}>Point camera at barcode</Text>
          </View>
        )}
      </>
    );
  };

  // Render Manual Entry Screen
  const renderManualScreen = () => (
    <View style={styles.centerContent}>
      <TouchableOpacity 
        style={styles.backButtonTop} 
        onPress={() => {setScreen('home'); setManualInput('');}}
      >
        <Text style={styles.backLink}>← Back</Text>
      </TouchableOpacity>

      <Text style={styles.title}>✏️ Enter Barcode</Text>
      <Text style={styles.subtitle}>Type the barcode number manually</Text>

      <TextInput
        style={styles.input}
        value={manualInput}
        onChangeText={setManualInput}
        placeholder="Enter barcode here..."
        placeholderTextColor="#666"
        keyboardType="default"
        autoFocus
      />

      <TouchableOpacity 
        style={[styles.button, !manualInput.trim() && styles.buttonDisabled]} 
        onPress={handleManualSubmit}
        disabled={!manualInput.trim()}
      >
        <Text style={styles.buttonText}>Submit Barcode</Text>
      </TouchableOpacity>
    </View>
  );

  // Main render logic
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

  return (
    <SafeAreaProvider>
      <SafeAreaView style={styles.container} edges={['top', 'bottom']}>
        {screen === 'home' && renderHomeScreen()}
        {screen === 'scanner' && renderScannerScreen()}
        {screen === 'manual' && renderManualScreen()}
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
    paddingHorizontal: 30,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    paddingBottom: 10,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
  },
  backLink: {
    fontSize: 18,
    color: '#00ff88',
    fontWeight: '600',
  },
  backButtonTop: {
    position: 'absolute',
    top: 20,
    left: 20,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 10,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 16,
    color: '#aaa',
    marginBottom: 40,
    textAlign: 'center',
  },
  primaryButton: {
    backgroundColor: '#00ff88',
    width: '100%',
    padding: 20,
    borderRadius: 15,
    alignItems: 'center',
    marginBottom: 15,
    flexDirection: 'row',
    justifyContent: 'center',
  },
  primaryButtonIcon: {
    fontSize: 28,
    marginRight: 12,
  },
  primaryButtonText: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1a1a2e',
  },
  secondaryButton: {
    backgroundColor: '#16213e',
    borderWidth: 2,
    borderColor: '#00ff88',
    width: '100%',
    padding: 20,
    borderRadius: 15,
    alignItems: 'center',
    marginBottom: 30,
    flexDirection: 'row',
    justifyContent: 'center',
  },
  secondaryButtonIcon: {
    fontSize: 28,
    marginRight: 12,
  },
  secondaryButtonText: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#00ff88',
  },
  loadingContainer: {
    backgroundColor: '#16213e',
    padding: 20,
    borderRadius: 15,
    alignItems: 'center',
    marginBottom: 20,
    borderWidth: 2,
    borderColor: '#00ff88',
  },
  loadingText: {
    fontSize: 16,
    color: '#00ff88',
    marginTop: 10,
    fontWeight: '600',
  },
  historyContainer: {
    width: '100%',
    flex: 1,
    marginTop: 20,
  },
  historyTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 15,
    textAlign: 'center',
  },
  historyItem: {
    backgroundColor: '#16213e',
    padding: 15,
    borderRadius: 12,
    marginBottom: 10,
    borderLeftWidth: 4,
    borderLeftColor: '#00ff88',
  },
  historyItemContent: {
    flexDirection: 'row',
  },
  productImage: {
    width: 70,
    height: 70,
    borderRadius: 8,
    marginRight: 12,
    backgroundColor: '#1a1a2e',
  },
  historyItemText: {
    flex: 1,
  },
  historyItemHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  historyType: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#00ff88',
    backgroundColor: '#1a1a2e',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  historyTime: {
    fontSize: 11,
    color: '#666',
  },
  productName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 4,
  },
  productBrand: {
    fontSize: 14,
    color: '#00ff88',
    marginBottom: 4,
    fontStyle: 'italic',
  },
  historyData: {
    fontSize: 13,
    color: '#aaa',
    fontFamily: 'monospace',
    marginTop: 2,
  },
  productSource: {
    fontSize: 11,
    color: '#666',
    marginTop: 4,
  },
  noProductInfo: {
    fontSize: 13,
    color: '#999',
    fontStyle: 'italic',
    marginTop: 4,
  },
  tapHint: {
    fontSize: 11,
    color: '#00ff88',
    textAlign: 'center',
    marginTop: 8,
    fontStyle: 'italic',
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
  instructionBox: {
    backgroundColor: 'rgba(0, 255, 136, 0.2)',
    margin: 20,
    padding: 15,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#00ff88',
  },
  instructionText: {
    fontSize: 16,
    color: '#00ff88',
    textAlign: 'center',
    fontWeight: '600',
  },
  input: {
    backgroundColor: '#16213e',
    width: '100%',
    padding: 18,
    borderRadius: 12,
    fontSize: 18,
    color: '#fff',
    marginBottom: 20,
    borderWidth: 2,
    borderColor: '#00ff88',
  },
  button: {
    backgroundColor: '#00ff88',
    width: '100%',
    padding: 18,
    borderRadius: 15,
    alignItems: 'center',
    marginTop: 10,
  },
  buttonDisabled: {
    backgroundColor: '#444',
    opacity: 0.5,
  },
  buttonText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1a1a2e',
  },
  backButton: {
    backgroundColor: 'transparent',
    borderWidth: 2,
    borderColor: '#00ff88',
    marginTop: 20,
    padding: 15,
    borderRadius: 12,
    width: '100%',
    alignItems: 'center',
  },
  backButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#00ff88',
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
