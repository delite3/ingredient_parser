/**
 * HomeScreen — landing page with Scan Barcode, Enter Manually, and Test Mode buttons.
 */
import React from 'react';
import { View, Text, TouchableOpacity, ActivityIndicator, StyleSheet } from 'react-native';
import { COLORS, SPACING, FONT_SIZES, BORDER_RADIUS } from '../constants/theme';

export default function HomeScreen({ navigation, route }) {
  const { loading, itemCount } = route.params ?? {};

  return (
    <View style={styles.centerContent}>
      <Text style={styles.title}>🔍 Barcode Scanner</Text>
      <Text style={styles.subtitle}>Choose an option</Text>

      <TouchableOpacity
        style={styles.primaryButton}
        onPress={() => navigation.navigate('Scanner')}
      >
        <Text style={styles.primaryButtonIcon}>📷</Text>
        <Text style={styles.primaryButtonText}>Scan Barcode</Text>
      </TouchableOpacity>

      <TouchableOpacity
        style={styles.secondaryButton}
        onPress={() => navigation.navigate('Manual')}
      >
        <Text style={styles.secondaryButtonIcon}>✏️</Text>
        <Text style={styles.secondaryButtonText}>Enter Manually</Text>
      </TouchableOpacity>

      <TouchableOpacity
        style={styles.testModeButton}
        onPress={() => navigation.navigate('TestMode')}
      >
        <Text style={styles.testModeButtonText}>🧪 Test Mode</Text>
      </TouchableOpacity>

      {loading && (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={COLORS.primary} />
          <Text style={styles.loadingText}>Looking up product...</Text>
        </View>
      )}

      {itemCount > 0 && (
        <Text style={styles.itemCount}>
          {itemCount} item{itemCount !== 1 ? 's' : ''} scanned
        </Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  centerContent: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: SPACING.xxl,
    backgroundColor: COLORS.background,
  },
  title: {
    fontSize: FONT_SIZES.title,
    fontWeight: 'bold',
    color: COLORS.textPrimary,
    marginBottom: 10,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: FONT_SIZES.lg,
    color: COLORS.textSecondary,
    marginBottom: SPACING.xxxl,
    textAlign: 'center',
  },
  primaryButton: {
    backgroundColor: COLORS.primary,
    width: '100%',
    padding: SPACING.xl,
    borderRadius: BORDER_RADIUS.xl,
    alignItems: 'center',
    marginBottom: SPACING.lg,
    flexDirection: 'row',
    justifyContent: 'center',
  },
  primaryButtonIcon: {
    fontSize: 28,
    marginRight: SPACING.md,
  },
  primaryButtonText: {
    fontSize: FONT_SIZES.xxl,
    fontWeight: 'bold',
    color: COLORS.background,
  },
  secondaryButton: {
    backgroundColor: COLORS.surface,
    borderWidth: 2,
    borderColor: COLORS.primary,
    width: '100%',
    padding: SPACING.xl,
    borderRadius: BORDER_RADIUS.xl,
    alignItems: 'center',
    marginBottom: SPACING.xxl,
    flexDirection: 'row',
    justifyContent: 'center',
  },
  secondaryButtonIcon: {
    fontSize: 28,
    marginRight: SPACING.md,
  },
  secondaryButtonText: {
    fontSize: FONT_SIZES.xxl,
    fontWeight: 'bold',
    color: COLORS.primary,
  },
  testModeButton: {
    backgroundColor: COLORS.transparent,
    borderWidth: 1,
    borderColor: '#444',
    width: '100%',
    padding: 14,
    borderRadius: BORDER_RADIUS.lg,
    alignItems: 'center',
    marginTop: 10,
  },
  testModeButtonText: {
    fontSize: FONT_SIZES.lg,
    color: '#888',
    fontWeight: '600',
  },
  loadingContainer: {
    backgroundColor: COLORS.surface,
    padding: SPACING.xl,
    borderRadius: BORDER_RADIUS.xl,
    alignItems: 'center',
    marginTop: SPACING.xl,
    borderWidth: 2,
    borderColor: COLORS.primary,
  },
  loadingText: {
    fontSize: FONT_SIZES.lg,
    color: COLORS.primary,
    marginTop: 10,
    fontWeight: '600',
  },
  itemCount: {
    fontSize: FONT_SIZES.md,
    color: COLORS.primary,
    marginTop: SPACING.xl,
    textAlign: 'center',
  },
});
