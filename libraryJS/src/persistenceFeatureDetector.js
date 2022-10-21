import { FeatureDetector } from "./featureDetector";

class PersistenceFeatureDetector extends FeatureDetector {
  constructor() {
    super();
  }

  peaksPersistence(data, x, y) {
    let peaksMeta = [];

    let indexD = data.map((d, i) => i);
    indexD = indexD
      .sort((a, b) => (data[a][y] > data[b][y] ? 1 : -1))
      .reverse();

    let indexPeaks = data.map(() => -1);

    for (const i of indexD) {
      let leftD = i > 0 && indexPeaks[i - 1] != -1;
      let rightD = i < data.length - 1 && indexPeaks[i + 1] != -1;

      let iLeft = leftD ? indexPeaks[i - 1] : -1;
      let iRight = rightD ? indexPeaks[i + 1] : -1;

      // Merge Left and Right Peaks
      if (leftD && rightD) {
        if (data[peaksMeta[iLeft].born][y] > data[peaksMeta[iRight].born][y]) {
          peaksMeta[iRight].died = i;
          peaksMeta[iLeft].right = peaksMeta[iRight].right;
          indexPeaks[peaksMeta[iLeft].right] = indexPeaks[i] = iLeft;
        } else {
          peaksMeta[iLeft].died = i;
          peaksMeta[iRight].left = peaksMeta[iLeft].left;
          indexPeaks[peaksMeta[iRight].left] = indexPeaks[i] = iRight;
        }
      }
      // New Peak Born
      else if (!leftD && !rightD) {
        peaksMeta.push({
          left: i,
          right: i,
          born: i,
          died: -1,
        });
        indexPeaks[i] = peaksMeta.length - 1;
      }
      // Merge to next peak left
      else if (leftD && !rightD) {
        peaksMeta[iLeft].right += 1;
        indexPeaks[i] = iLeft;
      }
      // Merge to next peak right
      else if (!leftD && rightD) {
        peaksMeta[iRight].left -= 1;
        indexPeaks[i] = iRight;
      }
    }

    // Calculate Persistences
    peaksMeta.forEach((e, i, arr) => {
      e.persistence = this.calculatePersistence(data, e, y);
      data[e.born].persistence = e.persistence;
    });

    // Sort by Persistences
    peaksMeta = peaksMeta
      .sort((a, b) => (a.persistence > b.persistence ? 1 : -1))
      .reverse();
    let peaksIndex = peaksMeta.map((p) => p.born);
    return this.getDataByIndex(data, peaksIndex, x, y);
  }

  getChartFeatures(timeSeriesData, metadata) {
    switch (metadata.featureMode) {
      case "peaks":
        return this.peaksPersistence(
          timeSeriesData,
          metadata["timeVar"],
          metadata["quantVar"]
        );
      case "valleys":
        return this.valleysPersistence(timeSeriesData, metadata["timeVar"], metadata["quantVar"]);
      case "peaksvalleys":
        return this.peaksValleysPersistence(timeSeriesData, metadata["timeVar"], metadata["quantVar"]);
      default:
        throw new Error(`Feature mode ${metadata.featureMode} not valid.`);
    }
  }
  // Utility Functions
  vSort(data, x) {
    return data.sort((a, b) => (a[x] > b[x] ? 1 : -1));
  }
  isPeak(data, i, y) {
    return data[i][y] > data[i - 1][y] && data[i][y] > data[i + 1][y];
  }
  isValley(data, i, y) {
    return data[i][y] < data[i - 1][y] && data[i][y] < data[i + 1][y];
  }
  derivative(data, x, y) {
    let dydx = [0];
    for (let i = 1; i < data.length; i++) {
      let dydxi = (data[i][y] - data[i - 1][y]) / (data[i][x] - data[i - 1][y]);
      dydx.push(dydxi);
    }
    dydx[0] = dydx[1];
    return dydx;
  }

  calculateProminence(data, peaksIndex, p, y) {
    let leftPeak = 0;
    let rightPeak = data.length - 1;

    // Get Left Peak Index > Peak
    for (let i = p - 1; i >= 0; --i) {
      if (data[peaksIndex[i]][y] > data[peaksIndex[p]][y]) {
        leftPeak = peaksIndex[i];
        break;
      }
    }

    // Get Right Peak Index > Peak
    for (let i = p + 1; i < peaksIndex.length; ++i) {
      if (data[peaksIndex[i]][y] > data[peaksIndex[p]][y]) {
        rightPeak = peaksIndex[i];
      }
    }

    let leftMin = data[peaksIndex[p]][y];
    let rightMin = data[peaksIndex[p]][y];

    // Get Left Minimum between Peaks
    for (let i = peaksIndex[p] - 1; i >= leftPeak; --i) {
      if (data[i][y] < leftMin) {
        leftMin = data[i][y];
      }
    }

    // Get Right Minimum between Peaks
    for (let i = peaksIndex[p] + 1; i < data.length; ++i) {
      if (data[i][y] < rightMin) {
        rightMin = data[i][y];
      }
    }

    // Get Lowest Contour Line (Greater of Left / Right Mins)
    let low = leftMin > rightMin ? leftMin : rightMin;
    // Prominence is Peak Height - Lowest Countour
    let prominence = data[peaksIndex[p]][y] - low;
    return prominence;
  }
  calculatePersistence(data, p, y) {
    return p.died == -1
      ? Number.POSITIVE_INFINITY
      : data[p.born][y] - data[p.died][y];
  }
  filterRecordsByDate(data, dateField, startDate, endDate) {
    return data.filter(
      (d) => d[dateField] >= startDate && d[dateField] <= endDate
    );
  }

  getDataByIndex(data, index, x) {
    let indexData = [];

    for (let i of index) {
      indexData.push(data[i]);
    }
    return indexData;
  }
}

export { PersistenceFeatureDetector };
