/**
 * TestModeScreen — choose from a list of sample barcodes to simulate a scan.
 */
import React, { useCallback } from 'react';
import { View, Text, TouchableOpacity, ScrollView, StyleSheet } from 'react-native';
import HeaderBar from '../components/HeaderBar';
import { TEST_BARCODES } from '../constants/testBarcodes';
import { useScanner } from '../context/ScannerContext';
import { COLORS, SPACING, FONT_SIZES, BORDER_RADIUS } from '../constants/theme';

export default function TestModeScreen({ navigation }) {
  const { processBarcode } = useScanner();

  const handleSelect = useCallback(
    (code) => {
      processBarcode('test', code, (item) => {
        navigation.navigate('Details', { item });
      });
    },
    [processBarcode, navigation],
  );

  return (
    <View style={styles.container}>
      <HeaderBar title="🧪 Test Mode" onBack={() => navigation.goBack()} />
      <Text style={styles.subtitle}>Tap a product to simulate scanning it</Text>

      <ScrollView contentContainerStyle={styles.list}>
        {TEST_BARCODES.map((item) => (
          <TouchableOpacity
            key={item.code}
            style={styles.item}
            onPress={() => handleSelect(item.code)}
          >
            <Text style={styles.emoji}>{item.emoji}</Text>
            <View style={styles.info}>
              <Text style={styles.name}>{item.name}</Text>
              <Text style={styles.code}>{item.code}</Text>
            </View>
            <Text style={styles.arrow}>›</Text>
          </TouchableOpacity>
        ))}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  subtitle: {
    fontSize: FONT_SIZES.md,
    color: COLORS.textSecondary,
    textAlign: 'center',
    paddingHorizontal: SPACING.xl,
    paddingBottom: SPACING.lg,
  },
  list: {
    paddingHorizontal: SPACING.lg,
    paddingBottom: SPACING.xxl,
  },
  item: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.surface,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.xl,
    marginBottom: 10,
    borderLeftWidth: 3,
    borderLeftColor: COLORS.primary,
  },
  emoji: {
    fontSize: 32,
    marginRight: SPACING.lg,
  },
  info: {
    flex: 1,
  },
  name: {
    fontSize: 17,
    fontWeight: 'bold',
    color: COLORS.textPrimary,
    marginBottom: SPACING.xs,
  },
  code: {
    fontSize: 13,
    color: COLORS.textSecondary,
    fontFamily: 'monospace',
  },
  arrow: {
    fontSize: 28,
    color: COLORS.primary,
    fontWeight: 'bold',
  },
});
