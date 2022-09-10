const AnnotatorService = {};

// eslint-disable-next-line no-unused-vars
require('cross-fetch/polyfill');

const TwinPeaks = require('../public/dist/twinpeaks');

const annotator = new TwinPeaks.Annotator();

const queryOptions = TwinPeaks.Annotator.getDefaultQueryOptions();

AnnotatorService.headlines = async (features, timeField, granularity, queryText) => annotator.headlines_point_query(features, timeField, granularity, queryText, queryOptions);

module.exports = AnnotatorService;
