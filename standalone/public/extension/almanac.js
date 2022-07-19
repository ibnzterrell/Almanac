// Anonymous function to avoid polluting the global namespace
(() => {
  let worksheet = {};
  let worksheets = [];
  let dataTableId = 0;
  let dataTable = {};

  let timeFieldIndex = -1;
  let quantFieldIndex = -1;
  let timeFieldName = '';
  let quantFieldName = '';

  let tabularData = [];

  function worksheetSelected() {
    worksheet = worksheets.find((w) => w.name === $('#worksheetSelect').val());
    loadWorksheetData();
  }

  function loadWorksheetData() {
    worksheet.getUnderlyingTablesAsync().then((tables) => {
      dataTableId = tables[0].id;

      worksheet.getUnderlyingTableDataAsync(dataTableId).then((table) => {
        dataTable = table;

        $('#timeFieldSelect').empty();
        $('#quantFieldSelect').empty();

        dataTable.columns.forEach((c) => {
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
      });
    });
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

  function selectMarks() {
    const features = window.TwinPeaks.Analyzer.peaks(tabularData, 'persistence', timeFieldName, quantFieldName).slice(0, 7);
    console.log(features);
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
      worksheetSelected();
    });
  });
})();
