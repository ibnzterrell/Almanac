const AnnotatorService = {};

// eslint-disable-next-line no-unused-vars
require('cross-fetch/polyfill');

const Almanac = require('../public/dist/almanac');

const annotator = new Almanac.Annotator();

const queryOptions = Almanac.Annotator.getDefaultQueryOptions();

AnnotatorService.headlines = async (features, timeField, granularity, queryText) => annotator.headlines_point_query(features, timeField, granularity, queryText, queryOptions);

module.exports = AnnotatorService;
