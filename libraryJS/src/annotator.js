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
  async headlines_point_query(
    data,
    dateField,
    granularity,
    query,
    options = {}
  ) {
    let params = {
      dateField: dateField,
      granularity: granularity,
      query: query
    };

    let dataPack = {
      data: data,
      params: params,
      options: options
    };

    console.log(dataPack);
    let resp = await this.postForResponse("/headline/point", dataPack);
    console.log(resp);
    resp.headlines = this.fixDateFormat(resp.headlines);

    if (resp.alternates != null) {
      resp.alternates = this.fixDateFormat(resp.alternates);
    }

    return resp;
  }
  async headlines_range_query(ranges, query, options = {}) {
    let params = {
      query: query
    };

    let dataPack = {
      ranges: ranges,
      params: params,
      options: options
    };

    console.log(dataPack);
    let resp = await this.postForResponse("/headline/range", dataPack);
    console.log(resp);
    resp.headlines = this.fixDateFormat(resp.headlines);

    if (resp.alternates != null) {
      resp.alternates = this.fixDateFormat(resp.alternates);
    }

    return resp;
  }
  async postForResponse(resource, dataPack) {
    let fetchOptions = {
      method: "POST",
      body: JSON.stringify(dataPack)
    };
    let url = this.basePath + resource;
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