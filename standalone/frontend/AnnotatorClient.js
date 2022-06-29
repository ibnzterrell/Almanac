const AnnotatorClient = {};

AnnotatorClient.basePath = window.location.href;

AnnotatorClient.postForResponse = async (resource, data, params = {}) => {
  console.log(data);
  const fetchOptions = {
    method: 'POST',
    body: JSON.stringify(data),
    headers: {
      'Content-Type': 'application/json',
    },
  };
  const url = `${AnnotatorClient.basePath + resource}?${new URLSearchParams(params).toString()}`;
  console.log(url);
  const response = await fetch(url, fetchOptions);
  return response.json();
};

AnnotatorClient.annotate = async (featuresF, timeFieldF, granularityF, queryTextF) => {
  const packedData = {
    features: featuresF,
    timeField: timeFieldF,
    granularity: granularityF,
    queryText: queryTextF,
  };
  return AnnotatorClient.postForResponse('annotate', packedData);
};

module.exports = AnnotatorClient;
