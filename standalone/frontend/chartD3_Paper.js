import * as d3 from 'd3';
import * as d3Annotation from 'd3-svg-annotation';
import * as d3Force from 'd3-force';
import * as TwinPeaks from '../public/dist/twinpeaks';
import AnnotatorClient from './AnnotatorClient';

const graphViewProps = ({
  width: 1920,
  height: 540,
  margin_top: 30,
  margin_bottom: 35,
  margin_left: 75,
  margin_right: 20,
  backgroundColor: 'white',
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
    }, [])
    .sort((a, b) => a.Month.getTime() - b.Month.getTime());
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
  const data = await d3.csv('/data/COVID_USConfirmed.csv', (d) => ({ Date: d3.timeParse('%Y-%m-%d')(d.date), Cases: parseInt(d.ConfirmedCases, 10) }));
  return data;
}

async function getUnemploymentData() {
  let data = await d3.csv('/data/UnemploymentRate.csv', (d) => ({ Month: d3.timeParse('%Y-%m-%d')(d.Date), UnemploymentRate: parseFloat(d.UnemploymentRate) }));
  data = data.filter((u) => !isNaN(u.UnemploymentRate));
  return data;
}

async function getEbolaData() {
  let data = await d3.csv('/data/ebola.csv');
  data = data.filter(
    (d) => d.Indicator
      === 'Cumulative number of confirmed, probable and suspected Ebola cases',
  )
    .map((d) => ({
      date: new Date(d.Date),
      cases: parseFloat(d.value),
    }))
    .reduce((sumarr, e, i, arr) => {
      const total = sumarr.find((f) => f.date.getTime() == e.date.getTime());
      if (total) total.cases += e.cases;
      else sumarr.push(e);

      return sumarr;
    }, [])
    .sort((a, b) => b.date - a.date)
    .reverse()
    .map((c, i, arr) => {
      let newCases = 0;
      if (i !== 0) {
        newCases = arr[i].cases - arr[i - 1].cases;
      } else {
        newCases = c.cases;
      }

      return {
        date: c.date,
        cases: newCases,
      };
    });
  return data;
}

async function getUkrainePolandBorderData() {
  let data = await d3.csv('/data/UkrainePolandBorder.csv');
  data = data.filter(
    (crossing) => crossing['Direction to / from Poland'] === 'arrival in Poland',
  )
    .map((c) => ({
      date: new Date(c.Date),
      people:
      parseInt(c['Number of persons (checked-in)'], 10)
      + parseInt(c['Number of people (evacuated)'], 10),
    }))
    .reduce((sumarr, e, i, arr) => {
      const total = sumarr.find((f) => f.date.getTime() === e.date.getTime());
      if (total) total.people += e.people;
      else sumarr.push(e);

      return sumarr;
    }, []);
  return data;
}

async function getMassShootingsData() {
  let data = await d3.csv('/data/mass_shootings.csv');
  data = data.map((s) => ({
    date: ((s2) => {
      const s3 = new Date(s2.date);
      s3.setDate(1);
      s3.setHours(0);
      s3.setMinutes(0);
      s3.setSeconds(0);
      s3.setMilliseconds(0);
      return s3;
    })(s),
    deaths: parseInt(s.fatalities, 10),
  }))
    .filter((s) => s.date.getTime() >= (new Date('2000').getTime()))
    .reduce((sumarr, e, i, arr) => {
      const total = sumarr.find((f) => f.date.getTime() == e.date.getTime());
      if (total) total.deaths += e.deaths;
      else sumarr.push(e);

      return sumarr;
    }, []);
  return data;
}

async function getHomeValuesData() {
  let data = await d3.csv('/data/homevalueindex.csv');
  data = data.map(
    (h) => {
      const states = [
        'Virginia',
        'California',
        'Florida',
        'Colorado',
        'New Jersey',
        'Arizona',
        'Texas',
        'New York',
        'Nevada',
        'Massachusetts',
        'North Carolina',
        'West Virginia',
        'Michigan',
        'Missouri',
        'Hawaii',
        'Idaho',
        'Indiana',
        'Tennessee',
        'Alabama',
        'South Carolina',
        'Illinois',
        'the District of Columbia',
        'Oklahoma',
        'Maryland',
        'Alaska',
        'New Mexico',
        'Oregon',
        'Georgia',
        'Montana',
        'Pennsylvania',
        'Utah',
        'Iowa',
        'Louisiana',
        'Connecticut',
        'Nebraska',
        'Wyoming',
        'Washington',
        'Vermont',
        'Wisconsin',
        'Arkansas',
        'Maine',
        'Minnesota',
        'Ohio',
        'Rhode Island',
        'Delaware',
        'Kansas',
        'New Hampshire',
        'Mississippi',
        'Kentucky',
        'South Dakota',
        'North Dakota',
      ];
      return {
        month: new Date(h.month),
        ZHVI:
          states
            .map((s) => parseFloat(h[s]))
            .reduce((a, b) => (isNaN(b) ? a : a + b), 0) / states.length,
      };
    },
  );
  return data;
}

async function getSimpsonsViewershipData() {
  let data = await d3.csv('/data/simpsons_episodes.csv');
  data = data.map((s) => ({
    month: ((s2) => {
      const s3 = new Date(s2.original_air_date);
      s3.setDate(1);
      s3.setHours(0);
      s3.setMinutes(0);
      s3.setSeconds(0);
      s3.setMilliseconds(0);
      return s3;
    })(s),
    viewers: parseFloat(s.us_viewers_in_millions),
  }))
    .filter((s) => s.month > new Date('2000'))
    .reduce((sumarr, e, i, arr) => {
      const total = sumarr.find((f) => f.month.getTime() == e.month.getTime());
      if (total) total.viewers += e.viewers;
      else sumarr.push(e);

      return sumarr;
    }, []);

  return data;
}

async function getEuroSwapData() {
  let data = await d3.csv('/data/EUR_SWAP_RATES.csv');
  data = data.map((e) => ({
    month: ((s2) => {
      const s3 = new Date(s2.DATE);
      s3.setDate(1);
      s3.setHours(0);
      s3.setMinutes(0);
      s3.setSeconds(0);
      s3.setMilliseconds(0);
      return s3;
    })(e),
    rate: parseFloat(e['1Y']),
  }))
    .reduce((avgarr, r) => {
      const avgidx = avgarr.findIndex(
        (a) => a.month.getTime() === r.month.getTime(),
      );
      if (avgidx !== -1) {
        avgarr[avgidx].total += r.rate;
        avgarr[avgidx].count += 1;
      } else {
        avgarr.push({
          month: r.month,
          total: r.rate,
          count: 1,
        });
      }

      return avgarr;
    }, [])
    .map((r) => ({
      month: r.month,
      rate: r.total / r.count,
    }));

  return data;
}

async function getTVNewsAfghanistanData() {
  let data = await d3.csv('/data/tvnews_afghanistan.csv');
  data = data.map((n) => ({
    date: new Date(n.date),
    screentime: parseFloat(n.screentime),
  }));
  return data;
}

async function getTeslaStockData() {
  let data = await d3.csv('/data/stocks_tesla.csv');
  data = data.map((n) => ({
    date: new Date(n.date),
    adjusted_close: parseFloat(n.adjusted_close),
  }))
    .filter((n) => n.date.getTime() >= new Date('2019').getTime() && n.date.getTime() <= new Date('2022-06-01').getTime());
  return data;
}

const svg = d3.select('#graphView').append('svg')
  .attr('preserveAspectRatio', 'xMinYMin meet')
  .attr('viewBox', `0 0 ${graphViewProps.width} ${graphViewProps.height}`)
  .classed('svg-content-responsive', true)
  // .attr('margin', graphViewProps.margin)
  .style('background-color', graphViewProps.backgroundColor)
  .on('dblclick', () => {
    annotationsContainer.buildAnnotations.editMode(!annotationsContainer.buildAnnotations.editMode()).update();
  });

const xAxisGroup = svg.append('g');
const yAxisGroup = svg.append('g');
const xAxisLabelGroup = svg.append('g');
const yAxisLabelGroup = svg.append('g');
const titleGroup = svg.append('g');
const line = svg.append('path');
const featureGroup = svg.append('g');
const annotGroup = svg.append('g');
const peakCircleRadius = 4;
// const annotCircleRadius = 4;
// const annotTriangeSize = 50;
let annotationsContainer = {};

function renderChart(data, datasetName, params) {
  // Erase existing chart
  line.selectAll('*').remove();
  xAxisGroup.selectAll('*').remove();
  yAxisGroup.selectAll('*').remove();
  xAxisLabelGroup.selectAll('*').remove();
  yAxisLabelGroup.selectAll('*').remove();
  titleGroup.selectAll('*').remove();
  featureGroup.selectAll('*').remove();
  annotGroup.selectAll('*').remove();

  // Render the Chart
  console.log(data);

  const xScale = d3.scaleTime().domain(d3.extent(
    data,
    (d) => d[[params.timeVar]],
  )).range([graphViewProps.margin_left, graphViewProps.width - graphViewProps.margin_right]);

  const yScale = d3.scaleLinear().domain(
    [0, d3.max(data, (d) => d[params.quantVar])],
  ).range([graphViewProps.height - graphViewProps.margin_bottom, graphViewProps.margin_top]);

  const xAxis = d3.axisBottom()
    .scale(xScale);

  const yAxis = d3.axisLeft()
    .scale(yScale);

  xAxisGroup.attr('transform', `translate(0,${graphViewProps.height - graphViewProps.margin_bottom})`).call(xAxis);
  yAxisGroup.attr('transform', `translate(${graphViewProps.margin_left}, 0)`).call(yAxis);

  xAxisLabelGroup.append('text')
    .attr('class', 'x label')
    .attr('text-anchor', 'middle')
    .attr('x', graphViewProps.width / 2)
    .attr('y', graphViewProps.height - 5)
    .attr('font-size', '1em')
    .text(params.xAxisLabel);

  yAxisLabelGroup.append('text')
    .attr('class', 'y label')
    .attr('text-anchor', 'middle')
    .attr('x', 0)
    .attr('y', 0)
    .attr('font-size', '1em')
    .text(params.yAxisLabel);

  yAxisLabelGroup
    .attr('transform', `translate(15, ${graphViewProps.height / 2}) rotate(-90)`);

  titleGroup.append('text')
    .attr('class', 'title')
    .attr('text-anchor', 'middle')
    .attr('x', graphViewProps.width / 2)
    .attr('y', graphViewProps.margin_top)
    .attr('font-size', '2em')
    .text(params.title);

  const lineGenerator = d3.line().x((d) => xScale(d[params.timeVar]))
    .y((d) => yScale(d[params.quantVar]));

  line.datum(data).attr(
    'd',
    (d) => lineGenerator(d),
  ).attr('fill', 'none').attr('stroke', 'blue');

  let featureData = TwinPeaks.Analyzer.features(data, params.featureMode, params.timeVar, params.quantVar).slice(0, params.numAnnotations);

  featureData = featureData.filter((f, i) => {
    if (datasetName === 'wildfire') {
      return f[params.timeVar].getTime() !== new Date('2017-07-01T07:00Z').getTime();
    }

    if (datasetName === 'massShootings') {
      return f[params.timeVar].getTime() !== new Date('2018-11-01T07:00Z').getTime() && f[params.timeVar].getTime() !== new Date('2018-02-01T08:00Z').getTime();
    }

    if (datasetName === 'tvnews_afghanistan') {
      return f[params.timeVar].getTime() !== new Date('2012-05-02').getTime() && f[params.timeVar].getTime() !== new Date('2010-06-23').getTime();
    }

    if (datasetName === 'unemployment') {
      return (f[params.timeVar].getTime() === new Date('Sat Feb 01 2020 00:00:00 GMT-0800 (Pacific Standard Time)').getTime()
      || f[params.timeVar].getTime() === new Date('Wed Apr 01 2020 00:00:00 GMT-0700 (Pacific Daylight Time)').getTime()
      || f[params.timeVar].getTime() === new Date('Thu Oct 01 2009 00:00:00 GMT-0700 (Pacific Daylight Time)').getTime()
      || f[params.timeVar].getTime() === new Date('Sun Jun 01 2003 00:00:00 GMT-0700 (Pacific Daylight Time)').getTime());
    }

    if (datasetName === 'simpsonsViewership') {
      return (f[params.timeVar].getTime() !== new Date('2000-02-01T08:00Z').getTime()
      && f[params.timeVar].getTime() !== new Date('2003-02-01T08:00Z').getTime()
      && f[params.timeVar].getTime() !== new Date('2003-11-01T08:00Z').getTime()
      && f[params.timeVar].getTime() !== new Date('2004-01-01T08:00Z').getTime()
      && f[params.timeVar].getTime() !== new Date('2005-05-01T07:00Z').getTime()
      && f[params.timeVar].getTime() !== new Date('2011-05-01T07:00Z').getTime()
      && f[params.timeVar].getTime() !== new Date('2011-11-01T07:00Z').getTime()
      && f[params.timeVar].getTime() !== new Date('2009-10-01T07:00Z').getTime()
      && f[params.timeVar].getTime() !== new Date('2015-01-01T08:00Z').getTime()
      && f[params.timeVar].getTime() !== new Date('2013-05-01T07:00Z').getTime()
      && f[params.timeVar].getTime() !== new Date('2014-01-01T08:00Z').getTime());
    }

    if (datasetName === 'ebola') {
      return (f[params.timeVar].getTime() === new Date('2014-10-29').getTime()
      || f[params.timeVar].getTime() === new Date('2014-11-12').getTime()
      || f[params.timeVar].getTime() === new Date('2014-12-10').getTime());
    }

    if (datasetName === 'ukrainePolandBorder') {
      return (f[params.timeVar].getTime() === new Date('2022-02-27').getTime()
      || f[params.timeVar].getTime() === new Date('2022-03-13').getTime());
    }

    if (datasetName === 'euroSwap') {
      return (f[params.timeVar].getTime() !== new Date('2007-12-01T08:00Z').getTime()
      && f[params.timeVar].getTime() !== new Date('2020-05-01T07:00Z').getTime());
    }

    return true;
  });
  let annotationData = {};

  console.log(featureData);

  function renderAnnotations() {
    annotGroup.selectAll('*').remove();
    console.log(annotationData);

    let aWidth = 200;
    if (datasetName === 'tvnews_afghanistan') {
      aWidth = 125;
    }
    if (datasetName === 'covid') {
      aWidth = 175;
    }
    if (datasetName === 'simpsonsViewership') {
      aWidth = 150;
    }
    const nodesFeatures = featureData.map((d) => ({ fx: xScale(d[params.timeVar]), fy: yScale(d[params.quantVar]), nodeType: 'feature' }));
    const nodesAnnotations = featureData.map((d) => ({
      x: xScale(d[params.timeVar]),
      y: yScale(d[params.quantVar]),
      ox: d[params.timeVar],
      oy: d[params.quantVar],
      nodeType: 'annotation',
    }));
    const nodesLine = data.map((d) => ({ fx: xScale(d[params.timeVar]), fy: yScale(d[params.quantVar]), nodeType: 'line' }));
    // const nodesAll = nodesFeatures.concat(nodesAnnotations).concat(nodesLine);
    const nodesAll = nodesFeatures.concat(nodesAnnotations);
    const nodeLinks = featureData.map((d, i) => ({ source: nodesFeatures[i], target: nodesAnnotations[i] }));

    annotationData.combined.sort(
      (a, b) => ((a[params.timeVar] > b[params.timeVar]) ? 1 : -1),
    );

    const annotations = annotationData.combined.map((f, i) => {
      const s = f.headlines[f.selection];
      const isoDate = d3.isoParse(s[params.timeVar]);

      const ax = xScale(isoDate);
      const ay = yScale(s[params.quantVar]);

      const disableAnnotation = f.enabled ? [] : ['connector', 'subject', 'note'];

      const nodeAnnot = nodesAnnotations.find((nA) => xScale(nA.ox) === ax);
      console.log(nodeAnnot);
      nodeAnnot.enabled = f.enabled;
      nodeAnnot.editing = f.editing;

      return {
        note: {
          title: s.main_headline,
          // TODO - Auto switch between month / day level
          // label: `${isoDate.toLocaleString('default', { month: 'short', day: 'numeric' })}, ${isoDate.getFullYear()}`,
          label: `${isoDate.toLocaleString('default', { month: 'short' })} ${isoDate.getFullYear()}`,
          wrap: aWidth,
        },
        x: ax,
        y: ay,
        dx: ax,
        dy: ay,
        connector: {
          end: 'arrow',
        },
        disable: disableAnnotation,
      };
    });

    // function annotCircleClicked(event, d) {
    //   console.log(d);
    //   console.log(annotationData);
    //   const h = annotationData.combined.find(
    //     (e) => new Date(e[params.timeVar]).getTime() === new Date(d.ox).getTime(),
    //   );
    //   console.log(h);

    //   h.editing = !h.editing;

    //   renderAnnotations();
    // }

    // function annotCircleMouseover(event, d) {
    //   d3.select(this).attr('r', annotCircleRadius * 2);
    // }

    // function annotCircleMouseout(event, d) {
    //   d3.select(this).attr('r', annotCircleRadius);
    // }

    // function annotPrevClicked(event, d) {
    //   const h = annotationData.combined.find(
    //     (e) => new Date(e[params.timeVar]).getTime() === new Date(d.ox).getTime(),
    //   );
    //   console.log(h);

    //   h.selection = (h.selection + h.headlines.length - 1) % h.headlines.length;

    //   renderAnnotations();
    // }

    // function annotNextClicked(event, d) {
    //   const h = annotationData.combined.find(
    //     (e) => new Date(e[params.timeVar]).getTime() === new Date(d.ox).getTime(),
    //   );
    //   console.log(h);

    //   h.selection = (h.selection + 1) % h.headlines.length;

    //   renderAnnotations();
    // }

    // function annotTriangleMouseover(event, d) {
    //   d3.select(this).attr('d', d3.symbol().type(d3.symbolTriangle).size(annotTriangeSize * 4));
    // }

    // function annotTriangleMouseout(event, d) {
    //   d3.select(this).attr('d', d3.symbol().type(d3.symbolTriangle).size(annotTriangeSize));
    // }

    const buildAnnotations = d3Annotation.annotation()
      .type(d3Annotation.annotationLabel)
      .annotations(annotations)
      .accessors({
        x: (d) => d.x, y: (d) => d.y, dx: (d) => d.dx, dy: (d) => d.dy,
      });

    let fontSize = 20;
    if (datasetName === 'massShootings') {
      fontSize = 15;
    }
    if (datasetName === 'tvnews_afghanistan') {
      fontSize = 16;
    }
    if (datasetName === 'covid') {
      fontSize = 16;
    }
    if (datasetName === 'simpsonsViewership') {
      fontSize = 15;
    }

    annotGroup.attr('class', 'annotation-group')
      .style('font-size', fontSize)
      .call(buildAnnotations);

    annotationsContainer.buildAnnotations = buildAnnotations;

    const annotCircles = annotGroup.selectAll('annotCircles')
      .data(nodesAnnotations)
      .enter()
      .append('circle')
      .attr('r', (d) => 0)
      .attr('cx', (d) => d.x)
      .attr('cy', (d) => d.y);
    //   .on('click', annotCircleClicked)
    //   .on('mouseover', annotCircleMouseover)
    //   .on('mouseout', annotCircleMouseout);

    // const annotPrev = annotGroup.selectAll('annotPrev')
    //   .data(nodesAnnotations)
    //   .enter()
    //   .append('path')
    //   .attr('d', (d) => d3.symbol().type(d3.symbolTriangle).size(d.enabled && d.editing ? annotTriangeSize : 0)())
    //   .attr('transform', (d) => `translate(${d.x + 10}, ${d.y}) rotate(90)`)
    //   .on('click', annotPrevClicked)
    //   .on('mouseover', annotTriangleMouseover)
    //   .on('mouseout', annotTriangleMouseout);

    // const annotNext = annotGroup.selectAll('annotNext')
    //   .data(nodesAnnotations)
    //   .enter()
    //   .append('path')
    //   .attr('d', (d) => d3.symbol().type(d3.symbolTriangle).size(d.enabled && d.editing ? annotTriangeSize : 0)())
    //   .attr('transform', (d) => `translate(${d.x - 10}, ${d.y}) rotate(-90)`)
    //   .on('click', annotNextClicked)
    //   .on('mouseover', annotTriangleMouseover)
    //   .on('mouseout', annotTriangleMouseout);

    function clamp(v, vMin, vMax) {
      return Math.max(vMin, Math.min(vMax, v));
    }

    function simTick() {
      annotCircles
        // eslint-disable-next-line no-return-assign
        .attr('cx', (d) => d.x = clamp(d.x, aWidth / 2 + graphViewProps.margin_left, graphViewProps.width - aWidth / 2))
        // eslint-disable-next-line no-return-assign
        .attr('cy', (d) => d.y = clamp(d.y, aWidth / 2 + graphViewProps.margin_top, graphViewProps.height - aWidth / 2 - graphViewProps.margin_bottom));

      // annotPrev
      //   .attr('transform', (d) => `translate(${d.x - 10}, ${d.y}) rotate(-90)`);

      // annotNext
      //   .attr('transform', (d) => `translate(${d.x + 10}, ${d.y}) rotate(90)`);

      buildAnnotations.annotations().forEach((d, i) => {
        const nodeAnnot = nodesAnnotations.find((nA) => xScale(nA.ox) === d.x);
        if (d.disable.length === 0) {
          d.dx = -d.x + nodeAnnot.x;
          d.dy = -d.y + nodeAnnot.y;
        }
      });
      buildAnnotations.update();
    }

    const simulation = d3Force.forceSimulation()
      // .force('x', d3.forceX().strength(0.1).x((d) => xScale(d.ox)))
      // .force('y', d3.forceY().strength(0.1).y((d) => yScale(d.oy)))
      // .force('charge', d3Force.forceManyBody().strength(-10))
      // .force('link', d3Force.forceLink().distance(5).id((d) => d.id))
      .force('collide', d3Force.forceCollide().radius(
        (d) => {
          if (d.nodeType === 'feature') {
            return 10;
          }
          if (d.nodeType === 'annotation') {
            if (d.enabled) {
              return aWidth / 2;
            }
            return 10;
          }
          if (d.nodeType === 'line') {
            return 10;
          }

          return 10;
        },
      ));

    // simulation.force('link').links(nodeLinks);
    simulation.nodes(nodesAll).on('tick', simTick);
  }

  function renderTable() {
    const tableView = document.getElementById('tableView');
    tableView.innerHTML = '';

    const tHead = tableView.createTHead();
    const tHeadRow = tHead.insertRow();
    const periodHead = tHeadRow.insertCell();
    const periodHeadText = document.createTextNode('period');
    periodHead.appendChild(periodHeadText);
    const headlineHead = tHeadRow.insertCell();
    const headlineHeadText = document.createTextNode('headlines');
    headlineHead.appendChild(headlineHeadText);

    const tBody = tableView.createTBody();
    annotationData.combined.map((f, i) => {
      const tRow = tBody.insertRow();
      const periodCell = tRow.insertCell();
      const periodCellText = document.createTextNode(f.date_period);
      periodCell.appendChild(periodCellText);
      const headlinesCell = tRow.insertCell();

      const headlineRankTable = document.createElement('table');
      headlineRankTable.setAttribute('class', 'headlineRankTable');
      const headlineTableHead = headlineRankTable.createTHead();
      const headlineTableHeadRow = headlineTableHead.insertRow();
      const rankHeadCell = headlineTableHeadRow.insertCell();
      rankHeadCell.setAttribute('class', 'rankCell');
      const rankHeadCellText = document.createTextNode('rank');
      rankHeadCell.appendChild(rankHeadCellText);

      const scoreHeadCell = headlineTableHeadRow.insertCell();
      const scoreHeadCellText = document.createTextNode('score');
      scoreHeadCell.setAttribute('class', 'scoreCell');
      scoreHeadCell.appendChild(scoreHeadCellText);

      const headlineHeadCell = headlineTableHeadRow.insertCell();
      const headlineHeadCellText = document.createTextNode('headline');
      headlineHeadCell.appendChild(headlineHeadCellText);

      const headlineRankBody = headlineRankTable.createTBody();
      f.headlines.map((h, i) => {
        const headlineTableRow = headlineRankBody.insertRow();

        const rankCell = headlineTableRow.insertCell();
        const rankCellText = document.createTextNode(i.toString());
        rankCell.setAttribute('class', 'rankCell');
        rankCell.appendChild(rankCellText);

        const scoreCell = headlineTableRow.insertCell();
        const scoreCellText = document.createTextNode(h.score.toFixed(4).toString());
        scoreCell.setAttribute('class', 'scoreCell');
        scoreCell.appendChild(scoreCellText);

        const headlineTableCell = headlineTableRow.insertCell();
        const headlineLink = document.createElement('a');
        const headlineCellText = document.createTextNode(h.main_headline);
        headlineLink.href = h.web_url;
        headlineLink.target = '_blank';
        headlineLink.appendChild(headlineCellText);
        headlineTableCell.appendChild(headlineLink);
      });
      headlinesCell.appendChild(headlineRankTable);
    });
  }

  function peakClicked(event, d) {
    console.log(d);
    console.log(annotationData);
    const h = annotationData.combined.find(
      (e) => new Date(e[params.timeVar]).getTime() === d[params.timeVar].getTime(),
    );
    console.log(h);

    if (h.enabled) {
      d3.select(this).attr('fill', 'red');
      h.enabled = false;
    } else {
      d3.select(this).attr('fill', 'green');
      h.enabled = true;
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
      annotationResults.combined = annotationResults.combined.map((a) => {
        // eslint-disable-next-line no-param-reassign
        a.enabled = true;
        a.selection = 0;
        a.editing = false;
        return a;
      });
      annotationData = annotationResults;
      renderAnnotations();
      renderTable();
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
    ebola: getEbolaData,
    ukrainePolandBorder: getUkrainePolandBorderData,
    massShootings: getMassShootingsData,
    homeValues: getHomeValuesData,
    simpsonsViewership: getSimpsonsViewershipData,
    euroSwap: getEuroSwapData,
    tvnews_afghanistan: getTVNewsAfghanistanData,
    stocks_tesla: getTeslaStockData,
  };

  const paramsMap = {
    wildfire: {
      timeVar: 'Month',
      quantVar: 'AcresBurned',
      granularity: 'month',
      query: '+california +wildfire',
      xAxisLabel: 'Month',
      yAxisLabel: 'Acres Burned',
      title: 'Acres Burned Monthly in Wildfires in California',
      featureMode: 'peaks',
      numAnnotations: 11,
    },
    approval: {
      timeVar: 'Month',
      quantVar: 'ApprovalRate',
      granularity: 'month',
      // query: '+president +("united states" states)',
      query: '+president',
      xAxisLabel: 'Month',
      yAxisLabel: 'Approval Rate',
      title: 'U.S. Presidential Approval Rate',
      featureMode: 'peaksvalleys',
      numAnnotations: 15,
    },
    covid: {
      timeVar: 'Date',
      quantVar: 'Cases',
      granularity: 'day',
      query: '+(coronavirus covid-19)',
      xAxisLabel: 'Date',
      yAxisLabel: 'New Cases',
      title: 'Daily New COVID-19 Cases in the United States',
      featureMode: 'peaks',
      numAnnotations: 8,
    },
    unemployment: {
      timeVar: 'Month',
      quantVar: 'UnemploymentRate',
      granularity: 'month',
      query: '+unemployment +(rate low) -briefing',
      xAxisLabel: 'Month',
      yAxisLabel: 'Unemployment Rate',
      title: 'Unemployment Rate in the United States',
      featureMode: 'peaksvalleys',
      numAnnotations: 11,
    },
    ebola: {
      timeVar: 'date',
      quantVar: 'cases',
      granularity: 'day',
      query: '+ebola +cases',
      xAxisLabel: 'Date',
      yAxisLabel: 'Cases',
      title: 'Daily Global New Ebola Cases',
      featureMode: 'peaks',
      numAnnotations: 7,
    },
    ukrainePolandBorder: {
      timeVar: 'date',
      quantVar: 'people',
      granularity: 'day',
      query: '+ukraine +poland +border',
      xAxisLabel: 'Date',
      yAxisLabel: 'People',
      title: 'Daily Border Crossings from Ukraine to Poland',
      featureMode: 'peaks',
      numAnnotations: 4,
    },
    massShootings: {
      timeVar: 'date',
      quantVar: 'deaths',
      granularity: 'month',
      query: '+shooting',
      xAxisLabel: 'Date',
      yAxisLabel: 'Cases',
      title: 'Monthly Deaths in Mass Shootings in the United States',
      featureMode: 'peaks',
      numAnnotations: 11,
    },
    homeValues: {
      timeVar: 'month',
      quantVar: 'ZHVI',
      granularity: 'month',
      query: '+housing +market',
      xAxisLabel: 'Month',
      yAxisLabel: 'Average Home Value Index',
      title: 'Average Home Value Index by Month in the United States',
      featureMode: 'peaks',
      numAnnotations: 3,
    },
    simpsonsViewership: {
      timeVar: 'month',
      quantVar: 'viewers',
      granularity: 'month',
      query: '+simpsons -briefly',
      xAxisLabel: 'Date',
      yAxisLabel: 'viewers (millions)',
      title: 'Simpsons Viewership by Month',
      featureMode: 'peaks',
      numAnnotations: 30,
    },
    euroSwap: {
      timeVar: 'month',
      quantVar: 'rate',
      granularity: 'month',
      query: '+euro +(bank currency debt)',
      xAxisLabel: 'Date',
      yAxisLabel: 'Euro 1-Yr Swap Rate',
      title: 'Euro 1-Yr Swap Rate by Month',
      featureMode: 'peaks',
      numAnnotations: 14,
    },
    tvnews_afghanistan: {
      timeVar: 'date',
      quantVar: 'screentime',
      granularity: 'day',
      query: '+afghanistan + "united states"',
      xAxisLabel: 'Date',
      yAxisLabel: 'Screentime (Seconds)',
      title: 'Amount of Coverage of Afghanistan on TV News',
      featureMode: 'peaks',
      numAnnotations: 10,
    },

    stocks_tesla: {
      timeVar: 'date',
      quantVar: 'adjusted_close',
      granularity: 'month',
      query: '+tesla',
      xAxisLabel: 'month',
      yAxisLabel: 'Closing Price (Adjusted)',
      title: 'Tesla Stock Price',
      featureMode: 'peaks',
      numAnnotations: 4,
    },
  };

  const getData = dataMap[datasetName];
  const params = paramsMap[datasetName];

  getData().then((data) => renderChart(data, datasetName, params));
}

Array.from(document.getElementsByName('dataset')).map((e) => e.addEventListener('click', datasetSelected));
datasetSelected();
