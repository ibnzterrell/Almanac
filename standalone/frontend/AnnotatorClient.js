const AnnotatorClient = {};

AnnotatorClient.basePath = window.location.href;

AnnotatorClient.postForResponse = async (resource, data) => {
  console.log(data);
  const fetchOptions = {
    method: 'POST',
    body: JSON.stringify(data),
    headers: {
      'Content-Type': 'application/json',
    },
  };
  const url = `${AnnotatorClient.basePath + resource}`;
  console.log(url);
  const response = await (await fetch(url, fetchOptions)).json();
  response.combined = response.headlines.map((h) => {
    const combination = {};
    combination[data.timeField] = h[data.timeField];
    combination.persistence = h.persistence;
    combination.date_period = h.date_period;
    combination.headlines = [h];
    const alternates = response.alternates.filter((a) => a.date_period === h.date_period);
    combination.headlines = combination.headlines.concat(alternates);
    return combination;
  });
  return response;
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
