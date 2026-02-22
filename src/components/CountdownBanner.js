/**
 * CountdownBanner — displayed after a barcode is scanned.
 * Shows the remaining seconds and an undo button.
 */
import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { COLORS, SPACING, FONT_SIZES, BORDER_RADIUS } from '../constants/theme';

export default function CountdownBanner({ seconds, onUndo }) {
  return (
    <View style={styles.container}>
      <Text style={styles.text}>
        ✓ Scanned! Opening details in {seconds}...
      </Text>
      <TouchableOpacity style={styles.undoButton} onPress={onUndo}>
        <Text style={styles.undoText}>↻ Undo & Rescan</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: COLORS.surface,
    margin: SPACING.xl,
    padding: SPACING.xl,
    borderRadius: BORDER_RADIUS.xl,
    borderWidth: 2,
    borderColor: COLORS.primary,
    alignItems: 'center',
  },
  text: {
    fontSize: FONT_SIZES.xl,
    color: COLORS.textPrimary,
    textAlign: 'center',
    marginBottom: SPACING.lg,
    fontWeight: '600',
  },
  undoButton: {
    backgroundColor: COLORS.danger,
    paddingVertical: SPACING.md,
    paddingHorizontal: SPACING.xxl,
    borderRadius: 10,
  },
  undoText: {
    fontSize: FONT_SIZES.lg,
    fontWeight: 'bold',
    color: COLORS.textPrimary,
  },
});
