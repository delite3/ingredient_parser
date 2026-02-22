/**
 * ManualEntryScreen — type a barcode number manually.
 */
import React, { useState, useCallback } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet } from 'react-native';
import { COLORS, SPACING, FONT_SIZES, BORDER_RADIUS } from '../constants/theme';

export default function ManualEntryScreen({ navigation, route }) {
  const { processBarcode } = route.params ?? {};
  const [input, setInput] = useState('');

  const handleSubmit = useCallback(() => {
    const trimmed = input.trim();
    if (!trimmed) return;
    processBarcode('manual', trimmed, (item) => {
      navigation.navigate('Details', { item });
    });
    setInput('');
  }, [input, processBarcode, navigation]);

  return (
    <View style={styles.centerContent}>
      <TouchableOpacity
        style={styles.backButtonTop}
        onPress={() => navigation.goBack()}
      >
        <Text style={styles.backLink}>← Back</Text>
      </TouchableOpacity>

      <Text style={styles.title}>✏️ Enter Barcode</Text>
      <Text style={styles.subtitle}>Type the barcode number manually</Text>

      <TextInput
        style={styles.input}
        value={input}
        onChangeText={setInput}
        placeholder="Enter barcode here..."
        placeholderTextColor={COLORS.textMuted}
        keyboardType="default"
        autoFocus
      />

      <TouchableOpacity
        style={[styles.button, !input.trim() && styles.buttonDisabled]}
        onPress={handleSubmit}
        disabled={!input.trim()}
      >
        <Text style={styles.buttonText}>Submit Barcode</Text>
      </TouchableOpacity>
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
  backButtonTop: {
    position: 'absolute',
    top: SPACING.xl,
    left: SPACING.xl,
  },
  backLink: {
    fontSize: FONT_SIZES.xl,
    color: COLORS.primary,
    fontWeight: '600',
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
  input: {
    backgroundColor: COLORS.surface,
    width: '100%',
    padding: SPACING.xl,
    borderRadius: BORDER_RADIUS.lg,
    fontSize: FONT_SIZES.xl,
    color: COLORS.textPrimary,
    marginBottom: SPACING.xl,
    borderWidth: 2,
    borderColor: COLORS.primary,
  },
  button: {
    backgroundColor: COLORS.primary,
    width: '100%',
    padding: SPACING.xl,
    borderRadius: BORDER_RADIUS.xl,
    alignItems: 'center',
    marginTop: 10,
  },
  buttonDisabled: {
    backgroundColor: '#444',
    opacity: 0.5,
  },
  buttonText: {
    fontSize: FONT_SIZES.xl,
    fontWeight: 'bold',
    color: COLORS.background,
  },
});
