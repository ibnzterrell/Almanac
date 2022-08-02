const fs = require('fs');

const dir = './public/dist';

if (!fs.existsSync(dir)) {
  fs.mkdirSync(dir);
}

fs.copyFile('../libraryJS/dist/index_bundle.umd.js', './public/dist/twinpeaks.js', (err) => {console.log(err)});
fs.copyFile('../../extensions-and-embedding-api/packages/api-extensions-js/dist-extensions/tableau.extensions.1.latest.js', './public/dist/tableau.extensions.js', (err) => {console.log(err)});