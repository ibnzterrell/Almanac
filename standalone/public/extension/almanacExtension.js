// Anonymous function to avoid polluting the global namespace
(() => {
  let worksheet = {};
  let worksheets = [];
  // const dataTableId = 0;
  let dataTable = {};

  let timeFieldIndex = -1;
  let quantFieldIndex = -1;
  let timeFieldName = '';
  let quantFieldName = '';

  let tabularData = [];

  let features = [];
  let annotations = [];
  let queryText = '';

  let annotator = {};
  let annotQueryOptions = {};

  function worksheetSelected() {
    worksheet = worksheets.find((w) => w.name === $('#worksheetSelect').val());
    loadWorksheetData();

    annotator = new window.TwinPeaks.Annotator();
    annotQueryOptions = window.TwinPeaks.Annotator.getDefaultQueryOptions();
  }

  function loadWorksheetData() {
    // worksheet.getUnderlyingTablesAsync().then((tables) => {
    //   console.log(tables);
    //   dataTableId = tables[0].id;

    //   worksheet.getUnderlyingTableDataAsync(dataTableId).then((table) => {
    //     dataTable = table;

    worksheet.getSummaryDataAsync().then(((table) => {
      dataTable = table;
      console.log(dataTable);
      $('#timeFieldSelect').empty();
      $('#quantFieldSelect').empty();

      dataTable.columns.forEach((c) => {
        console.log(c.fieldName);
        if (c.dataType === 'date' || c.dataType === 'date-time') {
          $('#timeFieldSelect').append($('<option/>', {
            value: c.index,
            text: c.fieldName,
          }));
        } else if (c.dataType === 'float' || c.dataType === 'integer') {
          $('#quantFieldSelect').append($('<option/>', {
            value: c.index,
            text: c.fieldName,
          }));
        }
      });

      $('#timeFieldSelect').on('change', columnSelected);
      $('#quantFieldSelect').on('change', columnSelected);
      columnSelected();
    }));
  }

  function columnSelected() {
    timeFieldIndex = $('#timeFieldSelect').val();
    timeFieldName = dataTable.columns[timeFieldIndex].fieldName;
    quantFieldIndex = $('#quantFieldSelect').val();
    quantFieldName = dataTable.columns[quantFieldIndex].fieldName;
    loadTimeSeriesData();
  }

  function loadTimeSeriesData() {
    tabularData = dataTable.data.map((row) => {
      const time = row[timeFieldIndex];
      const quant = row[quantFieldIndex];
      const point = {};
      point[timeFieldName] = time.nativeValue;
      point[quantFieldName] = quant.nativeValue;
      return point;
    });
    console.log(tabularData);
  }

  function lastMonth(date) {
    const lastMonthDate = new Date(date);
    lastMonthDate.setDate(1);
    lastMonthDate.setHours(-1);

    return new Date(Date.UTC(
      lastMonthDate.getUTCFullYear(),
      lastMonthDate.getUTCMonth(),
      lastMonthDate.getUTCDate(),
      lastMonthDate.getUTCHours(),
      lastMonthDate.getUTCMinutes(),
      lastMonthDate.getUTCSeconds(),
    ));
  }

  function selectMarks() {
    features = window.TwinPeaks.Analyzer.peaks(tabularData, 'persistence', timeFieldName, quantFieldName).slice(0, 7);
    console.log(features);

    const selectionCriteria = features.map((f) => ({
      fieldName: timeFieldName,
      value: { min: lastMonth(f[timeFieldName]), max: f[timeFieldName] },
    }));
    console.log(selectionCriteria);

    worksheet.clearSelectedMarksAsync().then(() => {
      selectionCriteria.forEach((c) => {
        worksheet.selectMarksByValueAsync([c], tableau.SelectionUpdateType.Add);
      });
    });
  }

  function annotateMarks() {
    queryText = $('#queryText').val();
    console.log(`Query Text: ${queryText}`);
    annotations = annotator.headlines_query(features, timeFieldName, 'month', queryText, annotQueryOptions).then((annotResults) => {
      console.log(annotResults);
    });
  }

  function debug() {
    worksheet.getParametersAsync().then((parameters) => {
      console.log(parameters);
    });
    worksheet.getFiltersAsync().then((filters) => {
      console.log(filters);
    });
    worksheet.getSelectedMarksAsync().then((marks) => {
      console.log(marks);
    });
    // worksheet.getSummaryDataAsync().then((data) => {
    //   console.log(data);
    // });
  }

  $(document).ready(() => {
    tableau.extensions.initializeAsync().then(() => {
      const dashboardName = tableau.extensions.dashboardContent.dashboard.name;

      worksheets = tableau.extensions.dashboardContent.dashboard.worksheets;

      $('#dashboardTitle').text(`Dashboard: ${dashboardName}`);

      worksheets.forEach((w) => {
        console.log(w.name);
        $('#worksheetSelect').append($('<option/>', {
          value: w.name,
          text: w.name,
        }));
      });

      $('#worksheetSelect').on('change', worksheetSelected);
      $('#selectMarksButton').on('click', selectMarks);
      $('#annotateMarksButton').on('click', annotateMarks);
      $('#debugButton').on('click', debug);
      worksheetSelected();
    });
  });
})();
