import pandas as pd
import json
import sqlalchemy as sa
from sqlalchemy.pool import SingletonThreadPool

from dotenv import load_dotenv
import os
from datetime import datetime, timedelta

load_dotenv()

startMonth = int(os.getenv("START_MONTH"))
startYear = int(os.getenv("START_YEAR"))

# yesterday = datetime.today() - timedelta(days=1)
# endMonth = yesterday.month
# endYear = yesterday.year

endMonth = int(os.getenv("END_MONTH"))
endYear = int(os.getenv("END_YEAR"))

fileRead = f"./data/NYT_Data_Clean_{startMonth}_{startYear}_to_{endMonth}_{endYear}.parquet"

print("Reading " + fileRead)
article_df = pd.read_parquet(fileRead)
article_df["pub_date"] = pd.to_datetime(article_df["pub_date"])


def proxyFile(url):
    nytPrefix = "https://www.nytimes.com/"
    nURL = url.replace(nytPrefix, "")
    nURL = nURL.replace("/", "_")
    if (not nURL.endswith(".html")):
        nURL += ".html"
    return nURL


def renderHTML(row):
    return f"""<html>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
    <h1>{row['main_headline']}</h1>
    <h3>{row['pub_date'].strftime('%A %B %m, %Y')}</h3>
    <p>{row['lead_paragraph']}</h3>
    </html>"""


# TODO: This is slow - figure out a faster way to do this
for index, row in article_df.iterrows():
    filename = f"./data/article/{proxyFile(row['web_url'])}"
    print(filename)
    with open(filename, "w") as f:
        html = renderHTML(row)
        print(html)
        f.write(html)
