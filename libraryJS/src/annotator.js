class Annotator {
    constructor(path = "https://api.chartannotator.hci.terrell.dev") {
      this.basePath = path;
    }
    setBasePath(newBasePath) {
      this.basePath = newBasePath;
    }
    static getDefaultQueryOptions() {
      return {
        alternates: true,
        topK: true,
        alphaFilter: true,
        decayWeighting: false,
        queryMode: "boolean",
        querySpace: "headlinewithlead",
        scoringSpace: "headline",
        consolidationMethod: "lemma_spaCy_sm",
        singleDocumentFilter: false,
        booleanFrequencies: false
      };
    }
    async searchTag(tagType, query) {
      let url = `${this.basePath}/search/${tagType}/${query}`;
      let fetchOptions = {
        method: "GET"
      };
      let response = await fetch(url, fetchOptions);
      return response.json();
    }
    async headlines_query(data, dateField, granularity, query, options = {}) {
      let data_container = {
        data: data
      };
      let parameters = {
        dateField: dateField,
        granularity: granularity,
        query: query
      };
  
      parameters = { ...parameters, ...options };
  
      console.log(data_container);
      let resp = await this.postForResponse(
        "/headline",
        data_container,
        parameters
      );
      console.log(resp);
      resp.headlines = this.fixDateFormat(resp.headlines);
  
      if (resp.alternates != null) {
        resp.alternates = this.fixDateFormat(resp.alternates);
      }
  
      return resp;
    }
    async headlines(dataA, dateA, methodA, tagA, granularityA) {
      let packedData = {
        data: dataA,
        date: dateA,
        method: methodA,
        tag: tagA,
        granularity: granularityA
      };
      let data = await this.postForResponse("/headline", packedData);
      return this.fixDateFormat(data.headlines);
    }
    async headlinesAlternate(dataA, dateA, methodA, tagA, granularityA) {
      let packedData = {
        data: dataA,
        date: dateA,
        method: methodA,
        tag: tagA,
        granularity: granularityA
      };
      let data = await this.postForResponse("/headline", packedData);
      console.log(data);
      return this.fixDateFormat(data.alternates);
    }
    async postForResponse(resource, data, params = {}) {
      let fetchOptions = {
        method: "POST",
        body: JSON.stringify(data)
      };
      let url =
        this.basePath + resource + "?" + new URLSearchParams(params).toString();
      console.log(url);
      let response = await fetch(url, fetchOptions);
      return response.json();
    }
  
    fixDateFormat(data) {
      for (let d of data) {
        d["pub_date"] = new Date(d["pub_date"]);
        d["publish_date"] = d["pub_date"].toDateString();
        //d["date"] = new Date(d["date"]);
      }
      return data;
    }
  
    arrayBreakHeadlines(data, maxLineLength) {
      for (let d of data) {
        d["main_headline_break"] = this.arrayBreak(
          d["main_headline"],
          maxLineLength
        );
      }
  
      return data;
    }
    arrayBreak(text, maxLineLength) {
      let words = text.split(" ");
      let s = "";
  
      let lines = [];
      for (const w of words) {
        if (s === "") {
          s = w;
        } else if ((s + w).length > maxLineLength) {
          lines.push(s);
          s = w;
        } else {
          s = s + " " + w;
        }
      }
      if (s !== "") {
        lines.push(s);
      }
      return lines;
    }
  }

  export {Annotator};