/**
 * HistoryScreen — grid view of all previously scanned items.
 */
import React, { useCallback } from 'react';
import { View, Text, TouchableOpacity, ScrollView, Image, Alert, StyleSheet } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useHistory } from '../context/HistoryContext';
import { COLORS, SPACING, FONT_SIZES, BORDER_RADIUS } from '../constants/theme';

export default function HistoryScreen({ navigation }) {
  const { scannedItems, removeItem } = useHistory();
  const insets = useSafeAreaInsets();

  const handlePress = useCallback(
    (item) => {
      navigation.navigate('Details', { item });
    },
    [navigation],
  );

  const handleDelete = useCallback(
    (item) => {
      Alert.alert(
        'Remove Item',
        `Remove "${item.product?.name || item.data}" from history?`,
        [
          { text: 'Cancel', style: 'cancel' },
          {
            text: 'Remove',
            style: 'destructive',
            onPress: () => removeItem(item.id),
          },
        ],
      );
    },
    [removeItem],
  );

  return (
    <View style={styles.container}>
      <View style={[styles.headerBar, { paddingTop: insets.top + SPACING.sm }]}>
        <Text style={styles.headerTitle}>History</Text>
      </View>

      {scannedItems.length === 0 ? (
        <View style={styles.emptyState}>
          <Text style={styles.emptyText}>No items scanned yet</Text>
          <Text style={styles.emptySubtext}>Scan or enter a barcode to get started</Text>
        </View>
      ) : (
        <ScrollView style={styles.scrollView}>
          <View style={styles.grid}>
            {scannedItems.map((item) => (
              <TouchableOpacity
                key={item.id}
                style={styles.gridItem}
                onPress={() => handlePress(item)}
                onLongPress={() => handleDelete(item)}
              >
                <TouchableOpacity
                  style={styles.deleteButton}
                  onPress={() => handleDelete(item)}
                  hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
                >
                  <Text style={styles.deleteIcon}>✕</Text>
                </TouchableOpacity>
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
                {item.product?.brand ? (
                  <Text style={styles.gridItemBrand} numberOfLines={1}>
                    {item.product.brand}
                  </Text>
                ) : null}
              </TouchableOpacity>
            ))}
          </View>
        </ScrollView>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  headerBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: SPACING.xl,
    paddingBottom: SPACING.lg,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.surface,
  },
  headerTitle: {
    fontSize: FONT_SIZES.xxl,
    fontWeight: 'bold',
    color: COLORS.textPrimary,
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: SPACING.xxxl,
  },
  emptyText: {
    fontSize: FONT_SIZES.xxl,
    color: COLORS.textPrimary,
    marginBottom: 10,
    fontWeight: '600',
  },
  emptySubtext: {
    fontSize: FONT_SIZES.md,
    color: COLORS.textSecondary,
    textAlign: 'center',
  },
  scrollView: {
    flex: 1,
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    padding: 10,
  },
  gridItem: {
    width: '48%',
    backgroundColor: COLORS.surface,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.md,
    margin: '1%',
    borderWidth: 2,
    borderColor: COLORS.background,
    position: 'relative',
  },
  deleteButton: {
    position: 'absolute',
    top: 6,
    right: 6,
    zIndex: 10,
    backgroundColor: 'rgba(255,60,60,0.85)',
    width: 24,
    height: 24,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  deleteIcon: {
    color: '#fff',
    fontSize: 13,
    fontWeight: 'bold',
    lineHeight: 15,
  },
  gridImage: {
    width: '100%',
    height: 120,
    borderRadius: BORDER_RADIUS.md,
    backgroundColor: COLORS.background,
    marginBottom: SPACING.sm,
  },
  gridImagePlaceholder: {
    width: '100%',
    height: 120,
    borderRadius: BORDER_RADIUS.md,
    backgroundColor: COLORS.background,
    marginBottom: SPACING.sm,
    justifyContent: 'center',
    alignItems: 'center',
  },
  placeholderText: {
    fontSize: 48,
  },
  gridItemName: {
    fontSize: FONT_SIZES.md,
    fontWeight: 'bold',
    color: COLORS.textPrimary,
    marginBottom: SPACING.xs,
    minHeight: 36,
  },
  gridItemBrand: {
    fontSize: FONT_SIZES.sm,
    color: COLORS.primary,
    fontStyle: 'italic',
  },
});
