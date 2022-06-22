const express = require('express');

const AnnotateRouter = express.Router();
const AnnotatorService = require('../services/AnnotatorService');

AnnotateRouter.post('/', async (req, res) => {
  console.log('body');
  console.log(req.body);

  const results = await AnnotatorService.headlines(
    req.body.features,
    req.body.timeField,
    req.body.granularity,
    req.body.queryText,
  );
  res.send(results);
});

module.exports = AnnotateRouter;
