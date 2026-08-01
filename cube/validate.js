#!/usr/bin/env node

const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

console.log('🔍 Starting MetricMind Cube.dev validation...');
console.log('='.repeat(60));

try {
  // Step 1: Check if npm dependencies are installed
  console.log('\n1️⃣ Checking npm dependencies...');
  const packageJsonPath = path.join(__dirname, 'package.json');
  const nodeModulesPath = path.join(__dirname, 'node_modules');
  if (!fs.existsSync(nodeModulesPath)) {
    console.log('   ⚠️ node_modules not found, running npm install...');
    execSync('npm install', { cwd: __dirname, stdio: 'inherit' });
  } else {
    console.log('   ✅ Dependencies found');
  }

  // Step 2: Check PostgreSQL container is running
  console.log('\n2️⃣ Checking PostgreSQL container...');
  try {
    const dockerPs = execSync('docker ps --filter "name=metricmind-postgres" --format "{{.Names}}"', { encoding: 'utf-8' }).trim();
    if (dockerPs.includes('metricmind-postgres')) {
      console.log('   ✅ PostgreSQL container running');
    } else {
      console.log('   ⚠️ Starting PostgreSQL container...');
      execSync('docker-compose up -d', { cwd: path.join(__dirname, '..'), stdio: 'inherit' });
    }
  } catch (err) {
    console.log('   ⚠️ Starting PostgreSQL...');
    execSync('docker-compose up -d', { cwd: path.join(__dirname, '..'), stdio: 'inherit' });
  }

  // Step 3: Validate Cube config files exist
  console.log('\n3️⃣ Checking Cube config files...');
  const requiredFiles = ['.env', 'cube.js', 'package.json'];
  requiredFiles.forEach(file => {
    const filePath = path.join(__dirname, file);
    if (fs.existsSync(filePath)) {
      console.log(`   ✅ ${file} found`);
    } else {
      console.log(`   ❌ ${file} missing!`);
      process.exit(1);
    }
  });

  // Step 4: Validate model files exist
  console.log('\n4️⃣ Checking semantic model files...');
  const modelFiles = [
    'dim_customer.js',
    'dim_date.js',
    'dim_employee.js',
    'dim_product.js',
    'dim_region.js',
    'fact_sales.js'
  ];
  modelFiles.forEach(file => {
    const filePath = path.join(__dirname, 'model', file);
    if (fs.existsSync(filePath)) {
      console.log(`   ✅ ${file} found`);
    } else {
      console.log(`   ❌ ${file} missing!`);
      process.exit(1);
    }
  });

  // Step 5: Quick syntax check on models
  console.log('\n5️⃣ Checking model syntax...');
  modelFiles.forEach(file => {
    const filePath = path.join(__dirname, 'model', file);
    try {
      require(filePath);
      console.log(`   ✅ ${file} valid`);
    } catch (err) {
      console.log(`   ❌ ${file} invalid: ${err.message}`);
      process.exit(1);
    }
  });

  console.log('\n' + '='.repeat(60));
  console.log('✅ ALL VALIDATIONS PASSED!');
  console.log('Cube.dev semantic layer is ready!');
  console.log('\nTo start Cube server:');
  console.log('  cd cube && npm run dev');
  console.log('\nThen open http://localhost:4000 to explore the Playground!');

} catch (error) {
  console.error('\n❌ Validation failed:', error.message);
  process.exit(1);
}
