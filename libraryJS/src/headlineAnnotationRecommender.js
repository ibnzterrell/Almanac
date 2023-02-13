import {AnnotationRecommender} from "./annotationRecommender.js";

class HeadlineAnnotationRecommender extends AnnotationRecommender {
    basePath = "https://api.chartannotator.hci.terrell.dev";

    constructor() {
        super();
    }

    postForReponse = async (resource, data) => {
        console.log(data);
        const fetchOptions = {
          method: 'POST',
          body: JSON.stringify(data),
          headers: {
            'Content-Type': 'application/json',
          },
        };
        const url = `${this.basePath + resource}`;
        console.log(url);
        const response = await (await fetch(url, fetchOptions)).json();
        return response;
      };
    
    async getAllAnnotations(features, metadata) {
      let parameters = {
        dateField: metadata.dateField,
        granularity: metadata.granularity,
        query: metadata.query,
      }

      let queryOptions = {
        alternates: true,
        mixed: true,
        topK: true,
        alphaFilter: true,
        decayWeighting: false,
        queryMode: "boolean",
        querySpace: "headlinewithlead",
        scoringSpace: "headline",
        consolidationMethod: "lemma_spaCy_sm",
        singleDocumentFilter: false,
        booleanFrequencies: false
      }

      let packedData = {
        data: features,
        params: parameters,
        options: queryOptions
      }

      let response = await this.postForReponse("/headline/point", packedData);
      response.combined = response.headlines.map((h) => {
        const combination = {};
        combination[metadata.dateField] = h[metadata.dateField];
        combination.persistence = h.persistence;
        combination.date_period = h.date_period;
        combination.headlines = [h];
        const alternates = response.alternates.filter((a) => a.date_period === h.date_period);
        combination.headlines = combination.headlines.concat(alternates);
        return combination;
      });
      return response;
    }

    async getAnnotations(feature, otherFeatures, metadata) {
      let allFeatures = [feature].concat(otherFeatures);
      
      let allAnnotations = await this.getAllAnnotations(allFeatures, metadata);

      let featureAnnotations = allAnnotations.combined.filter((a) => a.date_period === feature.date_period);

      return featureAnnotations;
    }
} 
export {HeadlineAnnotationRecommender};