/**
 * HeaderBar — simple top-bar with optional back button and title.
 * Respects the safe area inset so the bar never hides behind the status bar.
 */
import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { COLORS, SPACING, FONT_SIZES } from '../constants/theme';

export default function HeaderBar({ title, onBack }) {
  const insets = useSafeAreaInsets();

  return (
    <View style={[styles.container, { paddingTop: insets.top + SPACING.sm }]}>
      {onBack ? (
        <TouchableOpacity onPress={onBack}>
          <Text style={styles.backLink}>← Back</Text>
        </TouchableOpacity>
      ) : (
        <View style={{ width: 50 }} />
      )}
      <Text style={styles.title}>{title}</Text>
      <View style={{ width: 50 }} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: SPACING.xl,
    paddingBottom: SPACING.lg,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.surface,
  },
  title: {
    fontSize: FONT_SIZES.xxl,
    fontWeight: 'bold',
    color: COLORS.textPrimary,
  },
  backLink: {
    fontSize: FONT_SIZES.xl,
    color: COLORS.primary,
    fontWeight: '600',
  },
});
