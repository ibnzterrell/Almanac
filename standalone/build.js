const fs = require('fs');

const dir = './public/dist';

if (!fs.existsSync(dir)) {
  fs.mkdirSync(dir);
}

fs.copyFile('../libraryJS/dist/index_bundle.umd.js', './public/dist/twinpeaks.js', () => {});
