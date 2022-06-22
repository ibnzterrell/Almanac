const express = require('express');

const app = express();

const port = 3000;

const AnnotateRouter = require('./routes/AnnotateRouter');

app.use(express.json());
app.use(express.static('public'));

app.use('/annotate', AnnotateRouter);

app.listen(port, () => {
  console.log(`Standalone Annotator listening on port ${port}`);
});
