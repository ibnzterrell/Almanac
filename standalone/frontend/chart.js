import * as vega from 'vega';
import * as vegaLite from 'vega-lite';
import * as vl from 'vega-lite-api';
import * as vegaTooltip from 'vega-tooltip';
import * as vegaDatasets from 'vega-datasets';
import * as TwinPeaks from '../public/dist/twinpeaks';
import AnnotatorClient from './AnnotatorClient';

// setup API options
const options = {
  config: {
    // Vega-Lite default configuration
  },
  init: (view) => {
    // initialize tooltip handler
    view.tooltip(new vegaTooltip.Handler().call);
  },
  view: {
    // view constructor options
    // remove the loader if you don't want to default to vega-datasets!
    // loader: vega.loader({
    //   baseURL: "https://cdn.jsdelivr.net/npm/vega-datasets@2/",
    // }),
    renderer: 'canvas',
  },
};

// register vega and vega-lite with the API
vl.register(vega, vegaLite, options);

// End Vega-Lite Setup //

vegaDatasets['seattle-weather.csv']().then((weatherData) => {
  const lineChart = vl.markLine()
    .data(weatherData)
    .encode(
      vl.x().fieldT('date'),
      vl.y().fieldQ('precipitation'),
    )
    .width(1500)
    .height(500);

  const featureData = TwinPeaks.Analyzer.peaks(weatherData, 'prominence', 'date', 'precipitation').slice(0, 25);

  const featureMarks = lineChart.markCircle({ stroke: 'red' })
    .data(featureData)
    .encode(
      vl.x().fieldT('date'),
      vl.y().fieldQ('precipitation'),
    );

  AnnotatorClient.annotate(featureData, 'date', 'day', 'seattle').then(
    (results) => {
      console.log(results);
      const annotationData = results.headlines;

      const annotationTextProps = {
        align: 'left',
        dx: 10,
        dy: 0,
        angle: -30,
        radius: 5,
      };

      const textAnnotations = lineChart.markText(annotationTextProps, {})
        .data(annotationData)
        .encode(
          vl.x().fieldT('date'),
          vl.y().fieldQ('precipitation'),
          vl.text().fieldN('main_headline'),
          vl.href().fieldN('web_url'),
          vl.tooltip('publish_date'),
        );
      console.log(annotationData);
      vl.layer(lineChart, featureMarks, textAnnotations)
        .render()
        .then((viewElement) => {
        // render returns a promise to a DOM element containing the chart
        // viewElement.value contains the Vega View object instance
          document.getElementById('view').appendChild(viewElement);
        });
    },
  );
});
