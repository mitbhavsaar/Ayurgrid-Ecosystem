import fs from 'fs';
import path from 'path';
import { AYURVEDA_KNOWLEDGE } from './ayurknowledge/index.ts';

const outDir = './extracted_json';
if (!fs.existsSync(outDir)) {
  fs.mkdirSync(outDir, { recursive: true });
}

console.log('Starting export of TS knowledge-base collections...');

for (const [key, val] of Object.entries(AYURVEDA_KNOWLEDGE)) {
  if (typeof val === 'function') {
    console.log(`Skipping function key: ${key}`);
    continue;
  }
  if (!val) {
    console.log(`Skipping empty key: ${key}`);
    continue;
  }
  const filePath = path.join(outDir, `${key}.json`);
  fs.writeFileSync(filePath, JSON.stringify(val, null, 2));
  console.log(`Exported: ${key} -> ${filePath} (${Array.isArray(val) ? val.length + ' items' : 'object'})`);
}

console.log('All TS knowledge collections successfully exported to JSON!');
