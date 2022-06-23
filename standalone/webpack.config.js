const path = require('path');

module.exports = {
  entry: './frontend/chartD3.js',
  output: {
    filename: 'frontend.js',
    path: path.resolve(__dirname, 'public/dist'),
  },
  optimization: {
    minimize: false,
  },
};
