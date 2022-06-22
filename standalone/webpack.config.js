const path = require('path');

module.exports = {
  entry: './frontend/chart.js',
  output: {
    filename: 'frontend.js',
    path: path.resolve(__dirname, 'public/dist'),
  },
  optimization: {
    minimize: false,
  },
};
