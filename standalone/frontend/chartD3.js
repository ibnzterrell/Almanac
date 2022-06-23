import * as d3 from 'd3';
import * as TwinPeaks from '../public/dist/twinpeaks';
import AnnotatorClient from './AnnotatorClient';

const graphViewProps = ({
  width: 1120,
  height: 400,
  margin: 50,
  backgroundColor: 'whitesmoke',
});

async function getWildfireData() {
  const raw = await d3.csv(
    '/data/California_Fire_Incidents.csv',
    (d) => (d),
  );
  const data = raw.map((w) => ({
    Month: w.Started,
    AcresBurned: parseInt(w.AcresBurned, 10),
  }))
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

getApprovalData().then(
  (data) => {
    // Render the Chart
    console.log(data);
    const svg = d3.select('#graphView').append('svg')
      .attr('width', graphViewProps.width)
      .attr('height', graphViewProps.height)
      .attr('margin', graphViewProps.margin)
      .style('background-color', graphViewProps.backgroundColor);
    const xAxisGroup = svg.append('g');
    const yAxisGroup = svg.append('g');
    const line = svg.append('path');

    const xScale = d3.scaleTime().domain(d3.extent(
      data,
      (d) => d.Month,
    )).range([0, graphViewProps.width]);

    const yScale = d3.scaleLinear().domain(
      [0, d3.max(data, (d) => d.ApprovalRate)],
    ).range([graphViewProps.height, 0]);

    const xAxis = d3.axisBottom()
      .scale(xScale);

    const yAxis = d3.axisRight()
      .scale(yScale);

    xAxisGroup.call(xAxis);
    yAxisGroup.call(yAxis);

    const lineGenerator = d3.line().x((d) => xScale(d.Month))
      .y((d) => yScale(d.ApprovalRate));

    line.datum(data).attr(
      'd',
      (d) => lineGenerator(d),
    ).attr('fill', 'none').attr('stroke', 'blue');

    const featureData = TwinPeaks.Analyzer.peaks(data, 'persistence', 'Month', 'ApprovalRate').slice(0, 7);

    console.log(featureData);

    svg.selectAll('peaks')
      .data(featureData)
      .enter()
      .append('circle')
      .attr('fill', 'red')
      .attr('stroke', 'none')
      .attr('cx', (d) => xScale(d.Month))
      .attr('cy', (d) => yScale(d.ApprovalRate))
      .attr('r', 3);
  },
);
