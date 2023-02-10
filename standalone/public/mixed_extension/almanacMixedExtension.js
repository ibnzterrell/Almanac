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
  const annotations = [];
  let queryText = '';

  let annotator = {};
  let annotQueryOptions = {};

  const selectedMarkMetadata = [];

  function worksheetSelected() {
    worksheet = worksheets.find((w) => w.name === $('#worksheetSelect').val());
    loadWorksheetData();

    annotator = new window.TwinPeaks.Annotator();
    annotQueryOptions = window.TwinPeaks.Annotator.getDefaultQueryOptions();
  }

  function loadWorksheetData() {
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

  function autoSelectMarks() {
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

  function confirmMarkSet() {
    worksheet.getSelectedMarksAsync().then((marksCollection) => {
      console.log(marksCollection);
      marksTable = marksCollection.data[0];
      console.log(marksTable);
    });
  }

  function suggestAnnotations() {
    queryText = $('#queryText').val();
    console.log(`Query Text: ${queryText}`);
    annotator.headlines_point_query(features, timeFieldName, 'month', queryText, annotQueryOptions).then((annotResults) => {
      console.log(annotResults);
      mixed = annotResults.mixed;
      console.log(annotations);

      worksheet.getSelectedMarksAsync().then((marksCollection) => {
        console.log(marksCollection);
        marksTable = marksCollection.data[0];
        console.log(marksTable);

        timeFieldMarkIndex = marksTable.columns.findIndex((c) => c.fieldName === timeFieldName);
        quantFieldMarkIndex = marksTable.columns.findIndex((c) => c.fieldName === quantFieldName);

        $('#markList').empty();

        const mappedMarks = marksTable.data.map((m, mi) => {
          const mark = {};
          mark[timeFieldName] = m[timeFieldMarkIndex].nativeValue;
          mark[quantFieldName] = m[quantFieldMarkIndex].nativeValue;
          mark.tupleId = marksTable.marksInfo[mi].tupleId;
          mark.headlines = mixed.filter((a) => (new Date(a[timeFieldName])).getTime() === mark[timeFieldName].getTime());

          const markDiv = $('#markList').append(`<div class="markData">${timeFieldName}: ${mark[timeFieldName]}, ${quantFieldName}: ${mark[quantFieldName]}</div>`);
          console.log(mark.headlines);
          mark.headlines.forEach((h) => {
            markDiv.append(`<div class="headline">${h.main_headline}</div>`);
          });
          return mark;
        });
        console.log(mappedMarks);
      });
    });
  }

  function clearAnnotations() {
    worksheet.getAnnotationsAsync().then((annots) => {
      console.log(annots);
      annotations.forEach((a) => worksheet.removeAnnotationAsync(a));
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
      $('#autoSelectMarksButton').on('click', autoSelectMarks);
      $('#confirmMarkSetButton').on('click', confirmMarkSet);
      $('#suggestAnnotationsButton').on('click', suggestAnnotations);
      $('#clearAnnotationsButton').on('click', clearAnnotations);
      $('#debugButton').on('click', debug);
      worksheetSelected();
    });
  }
  $(document).ready(() => {
    $('#initializeButton').on('click', initialize);
  });
})();
