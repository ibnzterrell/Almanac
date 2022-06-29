import * as d3 from 'd3';
import * as d3Annotation from 'd3-svg-annotation';
import * as d3Force from 'd3-force';
import * as TwinPeaks from '../public/dist/twinpeaks';
import AnnotatorClient from './AnnotatorClient';

const graphViewProps = ({
  width: 1920,
  height: 540,
  margin: 50,
  backgroundColor: 'whitesmoke',
});

async function getWildfireData() {
  const raw = await d3.csv(
    '/data/California_Fire_Incidents.csv',
    (d) => ({
      Month: d.Started,
      AcresBurned: parseInt(d.AcresBurned, 10),
    }),
  );
  const data = raw
    .filter((x) => x.Month != '') // Remove Null Data
    .map((y) => {
      const d = new Date(y.Month);
      return {
        ...y,
        Month: new Date(d.getFullYear(), d.getMonth()),
      }; // Convert to Months
    })
    .filter((z) => z.Month >= new Date(2013, 0)) // Dataset is 2013 - 2020, Remove Invalid Dates
    .reduce((sumarr, e, i, arr) => {
      const total = sumarr.find((f) => f.Month.getTime() == e.Month.getTime());
      if (total) total.AcresBurned += e.AcresBurned;
      else sumarr.push(e);
      return sumarr;
    }, []);
  return data;
}

async function getApprovalData() {
  const data = await d3.csv(
    '/data/PresidentialApproval.csv',
    (d) => ({ Month: d3.timeParse('%Y-%m-%d')(d.Time), ApprovalRate: parseFloat(d.ApprovalRate) }),
  );
  return data;
}
async function getCovidData() {
  const data = await d3.csv('/data/COVID_USConfirmed.csv', (d) => ({ Month: d3.timeParse('%Y-%m-%d')(d.date), Cases: parseInt(d.ConfirmedCases, 10) }));
  return data;
}

async function getUnemploymentData() {
  const data = await d3.csv('/data/UnemploymentRate.csv', (d) => ({ Month: d3.timeParse('%Y-%m-%d')(d.Date), UnemploymentRate: parseFloat(d.UnemploymentRate) }));
  return data;
}

const svg = d3.select('#graphView').append('svg')
  .attr('preserveAspectRatio', 'xMinYMin meet')
  .attr('viewBox', `0 0 ${graphViewProps.width} ${graphViewProps.height}`)
  .classed('svg-content-responsive', true)
  .attr('margin', graphViewProps.margin)
  .style('background-color', graphViewProps.backgroundColor);
const xAxisGroup = svg.append('g');
const yAxisGroup = svg.append('g');
const line = svg.append('path');
const featureGroup = svg.append('g');
const annotGroup = svg.append('g');
const peakCircleRadius = 4;
const annotCircleRadius = 4;

function renderChart(data, params) {
  // Erase existing chart
  featureGroup.selectAll('*').remove();

  // Render the Chart
  console.log(data);

  const xScale = d3.scaleTime().domain(d3.extent(
    data,
    (d) => d[[params.timeVar]],
  )).range([0, graphViewProps.width]);

  const yScale = d3.scaleLinear().domain(
    [0, d3.max(data, (d) => d[params.quantVar])],
  ).range([graphViewProps.height, 0]);

  const xAxis = d3.axisTop()
    .scale(xScale);

  const yAxis = d3.axisRight()
    .scale(yScale);

  xAxisGroup.attr('transform', `translate(0,${graphViewProps.height})`).call(xAxis);
  yAxisGroup.call(yAxis);

  const lineGenerator = d3.line().x((d) => xScale(d[params.timeVar]))
    .y((d) => yScale(d[params.quantVar]));

  line.datum(data).attr(
    'd',
    (d) => lineGenerator(d),
  ).attr('fill', 'none').attr('stroke', 'blue');

  const featureData = TwinPeaks.Analyzer.peaks(data, 'persistence', params.timeVar, params.quantVar).slice(0, 7);
  let annotationData = {};

  console.log(featureData);

  function renderAnnotations() {
    annotGroup.selectAll('*').remove();
    console.log(annotationData);

    const xaWidth = graphViewProps.width / (featureData.length);

    const nodesFeatures = featureData.map((d) => ({ fx: xScale(d[params.timeVar]), fy: yScale(d[params.quantVar]) }));
    const nodesAnnotations = featureData.map((d) => ({ x: xScale(d[params.timeVar]), y: yScale(d[params.quantVar]), ox: d[params.timeVar] }));
    const nodeLinks = featureData.map((d, i) => ({ source: nodesFeatures[i], target: nodesAnnotations[i] }));

    const headlines = annotationData.headlines.sort(
      (a, b) => ((a[params.timeVar] > b[params.timeVar]) ? 1 : -1),
    );

    const annotations = headlines.map((f, i) => {
      const isoDate = d3.isoParse(f[params.timeVar]);

      const fx = xScale(isoDate);
      const fy = yScale(f[params.quantVar]);

      const xOffset = xaWidth * i + (xaWidth / 2);
      // Even / odd stagger Y
      const yOffset = (i % 2 === 1) ? 150 : 300;

      const ax = -fx + xOffset;
      const ay = -fy + yOffset;

      // console.log(fx, fy, ax, ay, f);

      const disableAnnotation = f.selected ? [] : ['connector', 'subject', 'note'];

      return {
        note: {
          title: f.main_headline,
          // TODO - Auto switch between month / day level
          // label: `${isoDate.toLocaleString('default', { month: 'short', day: 'numeric' })}, ${isoDate.getFullYear()}`,
          label: `${isoDate.toLocaleString('default', { month: 'short' })}, ${isoDate.getFullYear()}`,
          wrap: xaWidth,
        },
        x: fx,
        y: fy,
        dx: fx,
        dy: fy,
        connector: {
          end: 'arrow',
        },
        disable: disableAnnotation,
      };
    });

    const buildAnnotations = d3Annotation.annotation()
      .type(d3Annotation.annotationLabel)
      .annotations(annotations)
      .accessors({
        x: (d) => d.x, y: (d) => d.y, dx: (d) => d.dx, dy: (d) => d.dy,
      });

    annotGroup.attr('class', 'annotation-group')
      .call(buildAnnotations);

    const annotCircles = annotGroup.selectAll('annotCircles')
      .data(nodesAnnotations)
      .enter()
      .append('circle')
      .attr('r', annotCircleRadius)
      .attr('cx', (d) => d.x)
      .attr('cy', (d) => d.y);

    function simTick() {
      annotCircles
        .attr('cx', (d) => d.x)
        .attr('cy', (d) => d.y);

      buildAnnotations.annotations().forEach((d, i) => {
        const nodeAnnot = nodesAnnotations.find((nA) => xScale(nA.ox) === d.x);
        console.log(d);
        console.log(nodesAnnotations);
        console.log(nodeAnnot);
        d.dx = -d.x + nodeAnnot.x;
        d.dy = -d.y + nodeAnnot.y;
      });
      buildAnnotations.update();
    }

    const simulation = d3Force.forceSimulation()
      .force('link', d3Force.forceLink().id((d) => d.id))
      .force('charge', d3Force.forceManyBody())
      .force('center', d3Force.forceCenter(graphViewProps.width / 2, graphViewProps.height / 2));

    simulation.nodes(nodesAnnotations).on('tick', simTick);
    simulation.force('link').links(nodeLinks);
  }

  function peakClicked(event, d) {
    console.log(d);
    console.log(annotationData);
    const h = annotationData.headlines.find(
      (e) => new Date(e[params.timeVar]).getTime() === d[params.timeVar].getTime(),
    );
    console.log(h);

    if (!h.selected) {
      d3.select(this).attr('fill', 'green');
      h.selected = true;
    } else {
      d3.select(this).attr('fill', 'red');
      h.selected = false;
    }
    renderAnnotations();
  }

  function peakMouseover(event, d) {
    d3.select(this).attr('r', peakCircleRadius * 2);
  }

  function peakMouseout(event, d) {
    d3.select(this).attr('r', peakCircleRadius);
  }

  const featureCircles = featureGroup.selectAll('features')
    .data(featureData)
    .enter()
    .append('circle')
    .attr('fill', 'green')
    .attr('stroke', 'none')
    .attr('cx', (d) => xScale(d[params.timeVar]))
    .attr('cy', (d) => yScale(d[params.quantVar]))
    .attr('r', peakCircleRadius)
    .on('click', peakClicked)
    .on('mouseover', peakMouseover)
    .on('mouseout', peakMouseout);

  AnnotatorClient.annotate(featureData, params.timeVar, params.granularity, params.query).then(
    (annotationResults) => {
      // eslint-disable-next-line no-param-reassign
      annotationResults.headlines = annotationResults.headlines.map((a) => {
        // eslint-disable-next-line no-param-reassign
        a.selected = true;
        return a;
      });
      annotationData = annotationResults;
      renderAnnotations();
    },
  );
}

function datasetSelected() {
  console.log('Dataset changed');
  const datasetRadios = Array.from(document.getElementsByName('dataset'));
  const datasetName = datasetRadios.find((r) => r.checked === true).value;

  const dataMap = {
    wildfire: getWildfireData,
    approval: getApprovalData,
    covid: getCovidData,
    unemployment: getUnemploymentData,
  };

  const paramsMap = {
    wildfire: {
      timeVar: 'Month', quantVar: 'AcresBurned', granularity: 'month', query: '+california +wildfire',
    },
    approval: {
      timeVar: 'Month', quantVar: 'ApprovalRate', granularity: 'month', query: '+president +("united states" states)',
    },
    covid: {
      timeVar: 'Month', quantVar: 'Cases', granularity: 'day', query: '+(coronavirus covid-19)',
    },
    unemployment: {
      timeVar: 'Month', quantVar: 'UnemploymentRate', granularity: 'month', query: '+unemployment +"united states',
    },
  };

  const getData = dataMap[datasetName];
  const params = paramsMap[datasetName];

  getData().then((data) => renderChart(data, params));
}

document.getElementById('submitDataset').addEventListener('click', datasetSelected);
datasetSelected();
