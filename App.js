import { useState, useEffect, useRef } from 'react';
import { StyleSheet, Text, View, TouchableOpacity, TextInput, ScrollView, FlatList, ActivityIndicator, Image, Linking } from 'react-native';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';
import { CameraView, useCameraPermissions } from 'expo-camera';

export default function App() {
  const [permission, requestPermission] = useCameraPermissions();
  const [screen, setScreen] = useState('home'); // 'home', 'scanner', 'manual', 'history', 'details'
  const [previousScreen, setPreviousScreen] = useState('home'); // Track where we came from
  const [activeTab, setActiveTab] = useState('home'); // 'home', 'history'
  const [scannedItems, setScannedItems] = useState([]);
  const [selectedItem, setSelectedItem] = useState(null);
  const [manualInput, setManualInput] = useState('');
  const [scanned, setScanned] = useState(false);
  const [loading, setLoading] = useState(false);
  const [countdown, setCountdown] = useState(0);
  const countdownTimer = useRef(null);

  // Lookup product information from APIs
  const lookupProduct = async (barcode) => {
    try {
      // Try Open Food Facts first (great for food products)
      const offResponse = await fetch(`https://world.openfoodfacts.org/api/v0/product/${barcode}.json`);
      const offData = await offResponse.json();
      
      if (offData.status === 1 && offData.product) {
        const product = offData.product;
        return {
          name: product.product_name || 'Unknown Product',
          brand: product.brands || '',
          image: product.image_url || product.image_front_url || null,
          source: 'Open Food Facts',
          ingredients: product.ingredients_text || null,
          ingredientsList: product.ingredients || [],
          nutritionGrade: product.nutrition_grades || null,
          labels: product.labels || '',
          categories: product.categories || '',
          allergens: product.allergens || '',
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
  const addBarcode = async (type, data, fromScreen = 'scanner') => {
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
    setSelectedItem(newItem);
    setLoading(false);
    
    // Start countdown before auto-navigation (3 seconds)
    let timeLeft = 3;
    setCountdown(timeLeft);
    
    const timer = setInterval(() => {
      timeLeft--;
      if (timeLeft <= 0) {
        clearInterval(timer);
        // Auto-navigate to details screen after countdown
        setPreviousScreen(fromScreen);
        setScreen('details');
        setActiveTab('home');
        setScanned(false); // Reset scan state
        setCountdown(0);
      } else {
        setCountdown(timeLeft);
      }
    }, 1000);
    
    countdownTimer.current = timer;
  };

  // Cancel scan and undo
  const cancelScan = () => {
    if (countdownTimer.current) {
      clearInterval(countdownTimer.current);
    }
    setCountdown(0);
    setScanned(false);
    // Remove the last scanned item
    if (scannedItems.length > 0) {
      setScannedItems(scannedItems.slice(1));
    }
  };

  // Handle barcode scan (no cooldown, no alert)
  const handleBarCodeScanned = ({ type, data }) => {
    if (scanned || countdown > 0) return;
    
    setScanned(true);
    addBarcode(type, data, 'scanner');
  };

  // Handle manual entry submission
  const handleManualSubmit = () => {
    if (manualInput.trim()) {
      addBarcode('manual', manualInput.trim(), 'manual');
      setManualInput('');
      // addBarcode will navigate to details
    }
  };

  // Clean up timer on unmount
  useEffect(() => {
    return () => {
      if (countdownTimer.current) {
        clearInterval(countdownTimer.current);
      }
    };
  }, []);

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

      {/* Show count of scanned items */}
      {scannedItems.length > 0 && (
        <Text style={styles.itemCount}>
          {scannedItems.length} item{scannedItems.length !== 1 ? 's' : ''} scanned
        </Text>
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

        {/* Countdown with undo option */}
        {countdown > 0 && (
          <View style={styles.countdownContainer}>
            <Text style={styles.countdownText}>
              ✓ Scanned! Opening details in {countdown}...
            </Text>
            <TouchableOpacity 
              style={styles.undoButton} 
              onPress={cancelScan}
            >
              <Text style={styles.undoButtonText}>↻ Undo & Rescan</Text>
            </TouchableOpacity>
          </View>
        )}

        {!scanned && countdown === 0 && (
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

  // Render History Screen (Grid View)
  const renderHistoryScreen = () => (
    <View style={styles.fullScreen}>
      <View style={styles.headerBar}>
        <Text style={styles.headerTitle}>History</Text>
      </View>
      
      {scannedItems.length === 0 ? (
        <View style={styles.emptyState}>
          <Text style={styles.emptyStateText}>No items scanned yet</Text>
          <Text style={styles.emptyStateSubtext}>Scan or enter a barcode to get started</Text>
        </View>
      ) : (
        <ScrollView style={styles.historyScrollView}>
          <View style={styles.historyGrid}>
            {scannedItems.map((item) => (
              <TouchableOpacity 
                key={item.id}
                style={styles.gridItem}
                onPress={() => {
                  setSelectedItem(item);
                  setPreviousScreen('history');
                  setScreen('details');
                }}
              >
                {item.product?.image ? (
                  <Image 
                    source={{ uri: item.product.image }} 
                    style={styles.gridImage}
                    resizeMode="cover"
                  />
                ) : (
                  <View style={styles.gridImagePlaceholder}>
                    <Text style={styles.placeholderText}>📦</Text>
                  </View>
                )}
                <Text style={styles.gridItemName} numberOfLines={2}>
                  {item.product?.name || item.data}
                </Text>
                {item.product?.brand && (
                  <Text style={styles.gridItemBrand} numberOfLines={1}>
                    {item.product.brand}
                  </Text>
                )}
              </TouchableOpacity>
            ))}
          </View>
        </ScrollView>
      )}
    </View>
  );

  // Render Details Screen
  const renderDetailsScreen = () => {
    if (!selectedItem) {
      return (
        <View style={styles.centerContent}>
          <Text style={styles.text}>No item selected</Text>
          <TouchableOpacity 
            style={styles.button} 
            onPress={() => setScreen('home')}
          >
            <Text style={styles.buttonText}>Go Home</Text>
          </TouchableOpacity>
        </View>
      );
    }

    return (
      <View style={styles.fullScreen}>
        <View style={styles.headerBar}>
          <TouchableOpacity onPress={() => setScreen(previousScreen)}>
            <Text style={styles.backLink}>← Back</Text>
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Product Details</Text>
          <View style={{ width: 50 }} />
        </View>

        <ScrollView style={styles.detailsScrollView}>
          {/* Product Image */}
          {selectedItem.product?.image && (
            <Image 
              source={{ uri: selectedItem.product.image }} 
              style={styles.detailsImage}
              resizeMode="contain"
            />
          )}

          {/* Product Info */}
          <View style={styles.detailsCard}>
            <Text style={styles.detailsProductName}>
              {selectedItem.product?.name || 'Unknown Product'}
            </Text>
            
            {selectedItem.product?.brand && (
              <Text style={styles.detailsBrand}>{selectedItem.product.brand}</Text>
            )}
            
            <View style={styles.barcodeContainer}>
              <Text style={styles.barcodeLabel}>Barcode:</Text>
              <Text style={styles.barcodeValue}>{selectedItem.data}</Text>
            </View>

            {selectedItem.product?.nutritionGrade && (
              <View style={styles.nutritionGrade}>
                <Text style={styles.nutritionGradeText}>
                  Nutrition Grade: {selectedItem.product.nutritionGrade.toUpperCase()}
                </Text>
              </View>
            )}
          </View>

          {/* Ingredients */}
          {selectedItem.product?.ingredients && (
            <View style={styles.detailsCard}>
              <Text style={styles.sectionTitle}>🧪 Ingredients</Text>
              <Text style={styles.ingredientsText}>
                {selectedItem.product.ingredients}
              </Text>
            </View>
          )}

          {/* Allergens */}
          {selectedItem.product?.allergens && (
            <View style={styles.detailsCard}>
              <Text style={styles.sectionTitle}>⚠️ Allergens</Text>
              <Text style={styles.allergensText}>
                {selectedItem.product.allergens}
              </Text>
            </View>
          )}

          {/* Labels */}
          {selectedItem.product?.labels && (
            <View style={styles.detailsCard}>
              <Text style={styles.sectionTitle}>🏷️ Labels</Text>
              <Text style={styles.labelsText}>
                {selectedItem.product.labels}
              </Text>
            </View>
          )}

          {/* Categories */}
          {selectedItem.product?.categories && (
            <View style={styles.detailsCard}>
              <Text style={styles.sectionTitle}>📂 Categories</Text>
              <Text style={styles.categoriesText}>
                {selectedItem.product.categories}
              </Text>
            </View>
          )}

          {/* Go-UPC Link */}
          <TouchableOpacity 
            style={styles.externalLinkButton}
            onPress={() => Linking.openURL(`https://go-upc.com/search?q=${selectedItem.data}`)}
          >
            <Text style={styles.externalLinkText}>🔗 View on go-upc.com</Text>
          </TouchableOpacity>

          {/* Metadata */}
          <View style={styles.metadataCard}>
            <Text style={styles.metadata}>
              Scanned: {selectedItem.timestamp}
            </Text>
            <Text style={styles.metadata}>
              Type: {selectedItem.type.toUpperCase()}
            </Text>
            {selectedItem.product?.source && (
              <Text style={styles.metadata}>
                Source: {selectedItem.product.source}
              </Text>
            )}
          </View>
        </ScrollView>
      </View>
    );
  };

  // Render Tab Navigation
  const renderTabBar = () => (
    <View style={styles.tabBar}>
      <TouchableOpacity 
        style={[styles.tab, activeTab === 'home' && styles.activeTab]}
        onPress={() => {
          setActiveTab('home');
          setScreen('home');
        }}
      >
        <Text style={[styles.tabText, activeTab === 'home' && styles.activeTabText]}>
          🏠 Home
        </Text>
      </TouchableOpacity>

      <TouchableOpacity 
        style={[styles.tab, activeTab === 'history' && styles.activeTab]}
        onPress={() => {
          setActiveTab('history');
          setScreen('history');
        }}
      >
        <Text style={[styles.tabText, activeTab === 'history' && styles.activeTabText]}>
          📋 History ({scannedItems.length})
        </Text>
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
        {screen === 'history' && renderHistoryScreen()}
        {screen === 'details' && renderDetailsScreen()}
        
        {/* Show tab bar on home and history screens only */}
        {(screen === 'home' || screen === 'history') && renderTabBar()}
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
  countdownContainer: {
    backgroundColor: '#16213e',
    margin: 20,
    padding: 20,
    borderRadius: 15,
    borderWidth: 2,
    borderColor: '#00ff88',
    alignItems: 'center',
  },
  countdownText: {
    fontSize: 18,
    color: '#fff',
    textAlign: 'center',
    marginBottom: 15,
    fontWeight: '600',
  },
  undoButton: {
    backgroundColor: '#ff6b6b',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 10,
  },
  undoButtonText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
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
  itemCount: {
    fontSize: 14,
    color: '#00ff88',
    marginTop: 20,
    textAlign: 'center',
  },
  // Tab Bar Styles
  tabBar: {
    flexDirection: 'row',
    backgroundColor: '#16213e',
    borderTopWidth: 2,
    borderTopColor: '#00ff88',
  },
  tab: {
    flex: 1,
    padding: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  activeTab: {
    backgroundColor: '#1a1a2e',
    borderTopWidth: 3,
    borderTopColor: '#00ff88',
  },
  tabText: {
    fontSize: 14,
    color: '#aaa',
    fontWeight: '600',
  },
  activeTabText: {
    color: '#00ff88',
  },
  // Full Screen Layout
  fullScreen: {
    flex: 1,
  },
  headerBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    paddingBottom: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#16213e',
  },
  // Empty State
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 40,
  },
  emptyStateText: {
    fontSize: 20,
    color: '#fff',
    marginBottom: 10,
    fontWeight: '600',
  },
  emptyStateSubtext: {
    fontSize: 14,
    color: '#aaa',
    textAlign: 'center',
  },
  // History Grid Styles
  historyScrollView: {
    flex: 1,
  },
  historyGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    padding: 10,
  },
  gridItem: {
    width: '48%',
    backgroundColor: '#16213e',
    borderRadius: 12,
    padding: 12,
    margin: '1%',
    borderWidth: 2,
    borderColor: '#1a1a2e',
  },
  gridImage: {
    width: '100%',
    height: 120,
    borderRadius: 8,
    backgroundColor: '#1a1a2e',
    marginBottom: 8,
  },
  gridImagePlaceholder: {
    width: '100%',
    height: 120,
    borderRadius: 8,
    backgroundColor: '#1a1a2e',
    marginBottom: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  placeholderText: {
    fontSize: 48,
  },
  gridItemName: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 4,
    minHeight: 36,
  },
  gridItemBrand: {
    fontSize: 12,
    color: '#00ff88',
    fontStyle: 'italic',
  },
  // Details Screen Styles
  detailsScrollView: {
    flex: 1,
  },
  detailsImage: {
    width: '100%',
    height: 250,
    backgroundColor: '#16213e',
  },
  detailsCard: {
    backgroundColor: '#16213e',
    margin: 15,
    padding: 20,
    borderRadius: 12,
    borderLeftWidth: 4,
    borderLeftColor: '#00ff88',
  },
  detailsProductName: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 8,
  },
  detailsBrand: {
    fontSize: 18,
    color: '#00ff88',
    fontStyle: 'italic',
    marginBottom: 12,
  },
  barcodeContainer: {
    backgroundColor: '#1a1a2e',
    padding: 12,
    borderRadius: 8,
    marginTop: 8,
  },
  barcodeLabel: {
    fontSize: 12,
    color: '#aaa',
    marginBottom: 4,
  },
  barcodeValue: {
    fontSize: 18,
    color: '#fff',
    fontFamily: 'monospace',
    fontWeight: 'bold',
  },
  nutritionGrade: {
    backgroundColor: '#00ff88',
    padding: 10,
    borderRadius: 8,
    marginTop: 12,
    alignItems: 'center',
  },
  nutritionGradeText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1a1a2e',
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 12,
  },
  ingredientsText: {
    fontSize: 14,
    color: '#fff',
    lineHeight: 22,
  },
  allergensText: {
    fontSize: 14,
    color: '#ff6b6b',
    lineHeight: 22,
    fontWeight: '600',
  },
  labelsText: {
    fontSize: 14,
    color: '#00ff88',
    lineHeight: 22,
  },
  categoriesText: {
    fontSize: 14,
    color: '#aaa',
    lineHeight: 22,
  },
  externalLinkButton: {
    backgroundColor: '#16213e',
    margin: 15,
    padding: 18,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: '#00ff88',
    alignItems: 'center',
  },
  externalLinkText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#00ff88',
  },
  metadataCard: {
    backgroundColor: '#16213e',
    margin: 15,
    marginBottom: 30,
    padding: 15,
    borderRadius: 12,
  },
  metadata: {
    fontSize: 12,
    color: '#666',
    marginBottom: 4,
  },
});
