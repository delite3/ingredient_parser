/**
 * Open Food Facts / Open Beauty Facts / Open Products Facts lookup service.
 *
 * All three Open*Facts APIs share the same endpoint pattern and response shape.
 * We try each in order until we find a match, providing coverage across food,
 * cosmetics, and general consumer products.
 */

const SOURCES = [
  { baseUrl: 'https://world.openfoodfacts.org',    label: 'Open Food Facts' },
  { baseUrl: 'https://world.openbeautyfacts.org',  label: 'Open Beauty Facts' },
  { baseUrl: 'https://world.openproductsfacts.org', label: 'Open Products Facts' },
];

/**
 * Parse the raw API response into our normalised product shape.
 */
function parseProduct(product, sourceLabel) {
  return {
    name: product.product_name || 'Unknown Product',
    brand: product.brands || '',
    image: product.image_url || product.image_front_url || null,
    source: sourceLabel,
    ingredients: product.ingredients_text || null,
    ingredientsList: product.ingredients || [],
    nutritionGrade: product.nutrition_grades || null,
    novaGroup: product.nova_group || null,
    ecoScoreGrade: product.ecoscore_grade || null,
    additivesTags: product.additives_tags || [],
    ingredientsAnalysisTags: product.ingredients_analysis_tags || [],
    labels: product.labels || '',
    categories: product.categories || '',
    allergens: product.allergens || '',
  };
}

/**
 * Query a single Open*Facts API.
 * Returns the parsed product or null.
 */
async function querySource(barcode, { baseUrl, label }) {
  try {
    const url = `${baseUrl}/api/v0/product/${barcode}.json`;
    const response = await fetch(url);
    const data = await response.json();

    if (data.status === 1 && data.product) {
      return parseProduct(data.product, label);
    }
    return null;
  } catch (error) {
    console.warn(`[${label}] lookup error:`, error.message);
    return null;
  }
}

/**
 * Look up a product by barcode across all Open*Facts databases.
 * Tries each source in order; returns the first match or null.
 */
export async function lookupProduct(barcode) {
  for (const source of SOURCES) {
    const result = await querySource(barcode, source);
    if (result) return result;
  }
  return null;
}
