## Standalone Web App

### First Time:
Build the libary!

`npm run build` in libraryJS folder using rollup

Install prereqs for standalone:
`npm install` in this folder

### Build Instructions:
`npm run build` in this folder will also copy the earlier built libraryJS to dist and build web app using webpack 

`npm start` in this folder will run the webserver on http://localhost:3000

### High-Level Structure:
Analysis is done on frontend using Analyzer to find features. These features are then given to AnnotatorClient which POSTs these to the node.js AnnotatorService. AnnotatorService then POSTs to a Python API on Stanford's AWS backend to do headline annotation / lookup in the DB. Results are drawn in chart.js on frontend.