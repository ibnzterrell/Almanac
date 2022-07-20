## Standalone Web App

### First Time:
`npm install` in libraryJS folder

`npm run build` in libraryJS folder

`npm install` in standalone folder

### Build Instructions:
`npm run build` in standalone folder

`npm start` in standalone folder will run the webserver on http://localhost:3000

### High-Level Structure:
Analysis is done on frontend using Analyzer to find features. These features are then given to AnnotatorClient which POSTs these to the node.js AnnotatorService. AnnotatorService then POSTs to a Python API on Stanford's AWS backend to do headline annotation / lookup in the DB. Results are drawn in chart.js on frontend.

### Additional Instructions for Using the Tableau Extension
After running the standalone server, the extension host should be running as well. 

To add the extension to a Tableau dashboard:
Click "Extension" under "Objects", and in the "Add an extension window", click "Access Local Extensions". In the file picker dialog, select Almanac.trex in "/standalone/public/extension".

Using the extension:
Select the worksheet you're interested in, and select the columns you're interested in. 