// Automated barcode lookup test script
// Run with: npm test  OR  node test-barcodes.js

const testBarcodes = [
  { code: '3017620422003', name: 'Nutella' },
  { code: '5449000000996', name: 'Coca-Cola' },
  { code: '8000500310427', name: 'Ferrero Rocher' },
  { code: '7622300489908', name: 'Oreo' },
  { code: '4008400201542', name: 'Haribo Goldbears' },
  { code: '7314025346290', name: 'Scan from URL' },
  { code: '5000159484695', name: 'KitKat' },
  { code: '8710908518355', name: "Lay's" },
];

async function lookupBarcode(code) {
  const response = await fetch(`https://world.openfoodfacts.org/api/v0/product/${code}.json`);
  const data = await response.json();
  if (data.status === 1 && data.product) {
    const p = data.product;
    return {
      found: true,
      name: p.product_name || 'Unknown',
      brand: p.brands || '',
      ingredients: p.ingredients_text || null,
      ingredientCount: p.ingredients?.length || 0,
      hasImage: !!(p.image_url || p.image_front_url),
      nutritionGrade: p.nutrition_grades || null,
    };
  }
  return { found: false };
}

async function runTests() {
  console.log('\n🧪 Testing Barcode Lookup\n');
  console.log('='.repeat(50));

  let passed = 0;
  let failed = 0;

  for (const item of testBarcodes) {
    const label = item.name.padEnd(20);
    process.stdout.write(`Testing ${label} (${item.code})... `);

    try {
      const result = await lookupBarcode(item.code);

      if (result.found) {
        console.log('✅ PASS');
        console.log(`  └─ Found: ${result.name}`);
        if (result.brand)      console.log(`     Brand: ${result.brand}`);
        if (result.ingredients) console.log(`     Ingredients: ${result.ingredients.substring(0, 60)}...`);
        console.log(`     Ingredient count: ${result.ingredientCount}`);
        console.log(`     Has image: ${result.hasImage ? 'Yes' : 'No'}`);
        if (result.nutritionGrade) console.log(`     Nutrition grade: ${result.nutritionGrade.toUpperCase()}`);
        passed++;
      } else {
        console.log('❌ NOT FOUND');
        failed++;
      }
    } catch (err) {
      console.log(`❌ ERROR: ${err.message}`);
      failed++;
    }

    console.log('');
  }

  console.log('='.repeat(50));
  console.log(`Results: ${passed} passed, ${failed} failed out of ${testBarcodes.length} tests`);
  console.log('');
}

runTests().catch(console.error);
