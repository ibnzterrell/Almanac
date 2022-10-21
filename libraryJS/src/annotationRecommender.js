/**
 * @abstract
 */
 class AnnotationRecommender {
    constructor() {
        if (this.constructor == AnnotationRecommender) {
            throw new Error("Abstract classes can't be instantiated.");
        }
    }

    getAnnotations(feature, otherFeatures, metadata) {
        throw new Error("Method getAnnotations must be implemented.");
    }

    getAllAnnotations(features, metadata) {
        throw new Error("Method getAllAnnotations must be implemented.");
    }
}

export {AnnotationRecommender}