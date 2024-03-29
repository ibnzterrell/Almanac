// Anonymous function to avoid polluting the global namespace
(() => {
  let worksheet = {};
  let worksheets = [];
  // const dataTableId = 0;
  let dataTable = {};
  let marksTable = [];

  let timeFieldName = '';
  let quantFieldName = '';
  let timeFieldDataIndex = -1;
  let quantFieldDataIndex = -1;
  let timeFieldMarkIndex = -1;
  let quantFieldMarkIndex = -1;

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
        console.log(c.dataType);

        if (c.dataType === 'date' || c.dataType === 'date-time') {
          $('#timeFieldSelect').append($('<option/>', {
            value: c.index,
            text: c.fieldName,
          }));
        } else if (c.dataType === 'float' || c.dataType === 'int') {
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
    timeFieldDataIndex = $('#timeFieldSelect').val();
    timeFieldName = dataTable.columns[timeFieldDataIndex].fieldName;
    quantFieldDataIndex = $('#quantFieldSelect').val();
    quantFieldName = dataTable.columns[quantFieldDataIndex].fieldName;
    loadTimeSeriesData();
  }

  function loadTimeSeriesData() {
    tabularData = dataTable.data.map((row) => {
      const time = row[timeFieldDataIndex];
      const quant = row[quantFieldDataIndex];
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
    const numFeatures = $('#numFeatures').val();
    const featureMode = $('#featureModeSelect').val();

    features = window.TwinPeaks.Analyzer.features(
      tabularData,
      featureMode,
      timeFieldName,
      quantFieldName,
    ).slice(0, numFeatures);

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
    annotator.headlines_point_query(features, timeFieldName, 'month', queryText, annotQueryOptions).then((annotResults) => {
      annotations = annotResults.headlines;
      console.log(annotations);

      worksheet.getSelectedMarksAsync().then((marksCollection) => {
        console.log(marksCollection);
        marksTable = marksCollection.data[0];
        console.log(marksTable);

        timeFieldMarkIndex = marksTable.columns.findIndex((c) => c.fieldName === timeFieldName);
        quantFieldMarkIndex = marksTable.columns.findIndex((c) => c.fieldName === quantFieldName);

        let mappedMarks = marksTable.data.map((m, mi) => {
          const mark = {};
          mark[timeFieldName] = m[timeFieldMarkIndex].nativeValue;
          mark[quantFieldName] = m[quantFieldMarkIndex].nativeValue;
          mark.tupleId = marksTable.marksInfo[mi].tupleId;
          mark.annotation = annotations.find((a) => (new Date(a[timeFieldName])).getTime() === mark[timeFieldName].getTime());
          return mark;
        });
        console.log(mappedMarks);
        mappedMarks = mappedMarks.filter((m) => m.annotation !== undefined);

        mappedMarks.forEach((m, i) => {
          const markTupleInfo = { tupleId: m.tupleId };
          const annotationText = m.annotation.main_headline;
          return worksheet.annotateMarkAsync(markTupleInfo, annotationText);
        });
      });
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
    worksheet.getAnnotationsAsync().then((annotations) => {
      console.log(annotations);
      annotations.forEach((a) => worksheet.removeMarkAnnotationByIdAsync(a));
    });
  }

  function initialize() {
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
  }
  $(document).ready(() => {
    $('#initializeButton').on('click', initialize);
  });
})();
