const path = require('path');

const standaloneConfig = {
  entry: './frontend/chartD3_Paper.js',
  output: {
    filename: 'frontend.js',
    path: path.resolve(__dirname, 'public/dist'),
  },
  optimization: {
    minimize: false,
  },
};

const figureConfig = {
  entry: './frontend/chartD3_Paper_Figure.js',
  output: {
    filename: 'frontend_figure.js',
    path: path.resolve(__dirname, 'public/dist'),
  },
  optimization: {
    minimize: false,
  },
};

const mixedConfig = {
  entry: './frontend/chartD3_Mixed.js',
  output: {
    filename: 'frontend_mixed.js',
    path: path.resolve(__dirname, 'public/dist'),
  },
  optimization: {
    minimize: false,
  },
};

module.exports = [standaloneConfig, mixedConfig, figureConfig];
