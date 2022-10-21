/**
 * @abstract
 */
class FeatureDetector {
    constructor() {
        if (this.constructor == FeatureDetector) {
            throw new Error("Abstract classes can't be instantiated.");
        }
    }

    getChartFeatures(timeSeriesData, metadata) {
        throw new Error("Method getChartFeatures must be implemented.");
    }
}

export {FeatureDetector}