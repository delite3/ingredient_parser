/**
 * DetailsScreen — full product information for a scanned item.
 */
import React from 'react';
import { View, Text, TouchableOpacity, ScrollView, Image, Linking, StyleSheet } from 'react-native';
import HeaderBar from '../components/HeaderBar';
import { COLORS, SPACING, FONT_SIZES, BORDER_RADIUS } from '../constants/theme';

export default function DetailsScreen({ navigation, route }) {
  const { item } = route.params ?? {};

  if (!item) {
    return (
      <View style={styles.centerContent}>
        <Text style={styles.text}>No item selected</Text>
        <TouchableOpacity style={styles.button} onPress={() => navigation.goBack()}>
          <Text style={styles.buttonText}>Go Back</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const product = item.product;

  return (
    <View style={styles.container}>
      <HeaderBar title="Product Details" onBack={() => navigation.goBack()} />

      <ScrollView style={styles.scrollView}>
        {/* Product Image */}
        {product?.image && (
          <Image
            source={{ uri: product.image }}
            style={styles.image}
            resizeMode="contain"
          />
        )}

        {/* Product Info Card */}
        <View style={styles.card}>
          <Text style={styles.productName}>
            {product?.name || 'Unknown Product'}
          </Text>

          {product?.brand ? (
            <Text style={styles.brand}>{product.brand}</Text>
          ) : null}

          <View style={styles.barcodeBox}>
            <Text style={styles.barcodeLabel}>Barcode:</Text>
            <Text style={styles.barcodeValue}>{item.data}</Text>
          </View>

          {product?.nutritionGrade ? (
            <View style={styles.nutritionGrade}>
              <Text style={styles.nutritionGradeText}>
                Nutrition Grade: {product.nutritionGrade.toUpperCase()}
              </Text>
            </View>
          ) : null}
        </View>

        {/* Ingredients */}
        {(product?.ingredients || (product?.ingredientsList && product.ingredientsList.length > 0)) ? (
          <View style={styles.card}>
            <Text style={styles.sectionTitle}>🧪 Ingredients</Text>
            {product?.ingredients ? (
              <Text style={styles.ingredientsText}>{product.ingredients}</Text>
            ) : null}
            {product?.ingredientsList && product.ingredientsList.length > 0 && !product?.ingredients ? (
              <Text style={styles.ingredientsText}>
                {product.ingredientsList.map((ing) => ing.text || ing.id?.replace('en:', '') || '').filter(Boolean).join(', ')}
              </Text>
            ) : null}
            {product?.ingredientsList && product.ingredientsList.length > 0 ? (
              <View style={styles.ingredientChips}>
                {product.ingredientsList.map((ing, index) => {
                  const name = ing.text || ing.id?.replace('en:', '') || `#${index + 1}`;
                  return (
                    <View key={ing.id || index} style={styles.ingredientChip}>
                      <Text style={styles.ingredientChipText}>{name}</Text>
                    </View>
                  );
                })}
              </View>
            ) : null}
          </View>
        ) : null}

        {/* Additives */}
        {product?.additivesTags && product.additivesTags.length > 0 ? (
          <View style={styles.card}>
            <Text style={styles.sectionTitle}>⚗️ Additives</Text>
            <View style={styles.ingredientChips}>
              {product.additivesTags.map((tag) => (
                <View key={tag} style={[styles.ingredientChip, styles.additiveChip]}>
                  <Text style={styles.additiveChipText}>{tag.replace('en:', '')}</Text>
                </View>
              ))}
            </View>
          </View>
        ) : null}

        {/* Allergens */}
        {product?.allergens ? (
          <View style={styles.card}>
            <Text style={styles.sectionTitle}>⚠️ Allergens</Text>
            <Text style={styles.allergensText}>{product.allergens}</Text>
          </View>
        ) : null}

        {/* Labels */}
        {product?.labels ? (
          <View style={styles.card}>
            <Text style={styles.sectionTitle}>🏷️ Labels</Text>
            <Text style={styles.labelsText}>{product.labels}</Text>
          </View>
        ) : null}

        {/* Categories */}
        {product?.categories ? (
          <View style={styles.card}>
            <Text style={styles.sectionTitle}>📂 Categories</Text>
            <Text style={styles.categoriesText}>{product.categories}</Text>
          </View>
        ) : null}

        {/* External Link */}
        <TouchableOpacity
          style={styles.externalLinkButton}
          onPress={() => Linking.openURL(`https://go-upc.com/search?q=${item.data}`)}
        >
          <Text style={styles.externalLinkText}>🔗 View on go-upc.com</Text>
        </TouchableOpacity>

        {/* Metadata */}
        <View style={styles.metadataCard}>
          <Text style={styles.metadata}>Scanned: {item.timestamp}</Text>
          <Text style={styles.metadata}>Type: {item.type.toUpperCase()}</Text>
          {product?.source ? (
            <Text style={styles.metadata}>Source: {product.source}</Text>
          ) : null}
        </View>
      </ScrollView>
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
  text: {
    fontSize: 22,
    color: COLORS.textPrimary,
    textAlign: 'center',
    marginBottom: SPACING.lg,
    fontWeight: '600',
  },
  button: {
    backgroundColor: COLORS.primary,
    width: '100%',
    padding: SPACING.xl,
    borderRadius: BORDER_RADIUS.xl,
    alignItems: 'center',
  },
  buttonText: {
    fontSize: FONT_SIZES.xl,
    fontWeight: 'bold',
    color: COLORS.background,
  },
  scrollView: {
    flex: 1,
  },
  image: {
    width: '100%',
    height: 250,
    backgroundColor: COLORS.surface,
  },
  card: {
    backgroundColor: COLORS.surface,
    margin: SPACING.lg,
    padding: SPACING.xl,
    borderRadius: BORDER_RADIUS.lg,
    borderLeftWidth: 4,
    borderLeftColor: COLORS.primary,
  },
  productName: {
    fontSize: FONT_SIZES.xxxl,
    fontWeight: 'bold',
    color: COLORS.textPrimary,
    marginBottom: SPACING.sm,
  },
  brand: {
    fontSize: FONT_SIZES.xl,
    color: COLORS.primary,
    fontStyle: 'italic',
    marginBottom: SPACING.md,
  },
  barcodeBox: {
    backgroundColor: COLORS.background,
    padding: SPACING.md,
    borderRadius: BORDER_RADIUS.md,
    marginTop: SPACING.sm,
  },
  barcodeLabel: {
    fontSize: FONT_SIZES.sm,
    color: COLORS.textSecondary,
    marginBottom: SPACING.xs,
  },
  barcodeValue: {
    fontSize: FONT_SIZES.xl,
    color: COLORS.textPrimary,
    fontFamily: 'monospace',
    fontWeight: 'bold',
  },
  nutritionGrade: {
    backgroundColor: COLORS.primary,
    padding: 10,
    borderRadius: BORDER_RADIUS.md,
    marginTop: SPACING.md,
    alignItems: 'center',
  },
  nutritionGradeText: {
    fontSize: FONT_SIZES.lg,
    fontWeight: 'bold',
    color: COLORS.background,
  },
  sectionTitle: {
    fontSize: FONT_SIZES.xl,
    fontWeight: 'bold',
    color: COLORS.textPrimary,
    marginBottom: SPACING.md,
  },
  ingredientsText: {
    fontSize: FONT_SIZES.md,
    color: COLORS.textPrimary,
    lineHeight: 22,
    marginBottom: SPACING.md,
  },
  ingredientChips: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginTop: SPACING.sm,
  },
  ingredientChip: {
    backgroundColor: COLORS.background,
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 14,
    marginRight: 6,
    marginBottom: 6,
    borderWidth: 1,
    borderColor: COLORS.primary,
  },
  ingredientChipText: {
    fontSize: FONT_SIZES.sm,
    color: COLORS.textPrimary,
  },
  additiveChip: {
    borderColor: '#ff6b35',
    backgroundColor: 'rgba(255, 107, 53, 0.12)',
  },
  additiveChipText: {
    fontSize: FONT_SIZES.sm,
    color: '#ff6b35',
    fontWeight: '600',
  },
  allergensText: {
    fontSize: FONT_SIZES.md,
    color: COLORS.danger,
    lineHeight: 22,
    fontWeight: '600',
  },
  labelsText: {
    fontSize: FONT_SIZES.md,
    color: COLORS.primary,
    lineHeight: 22,
  },
  categoriesText: {
    fontSize: FONT_SIZES.md,
    color: COLORS.textSecondary,
    lineHeight: 22,
  },
  externalLinkButton: {
    backgroundColor: COLORS.surface,
    margin: SPACING.lg,
    padding: SPACING.xl,
    borderRadius: BORDER_RADIUS.lg,
    borderWidth: 2,
    borderColor: COLORS.primary,
    alignItems: 'center',
  },
  externalLinkText: {
    fontSize: FONT_SIZES.lg,
    fontWeight: 'bold',
    color: COLORS.primary,
  },
  metadataCard: {
    backgroundColor: COLORS.surface,
    margin: SPACING.lg,
    marginBottom: SPACING.xxl,
    padding: SPACING.lg,
    borderRadius: BORDER_RADIUS.lg,
  },
  metadata: {
    fontSize: FONT_SIZES.sm,
    color: COLORS.textMuted,
    marginBottom: SPACING.xs,
  },
});
