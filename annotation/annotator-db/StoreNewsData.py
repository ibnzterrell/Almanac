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


def rank_array(df, column):
    for uri, arr in zip(df["uri"], df[column]):
        arr = json.loads(arr)
        for i, a in enumerate(arr):
            rank = i + 1
            yield (uri, rank, a)


def rank_df(df, df_col, rank_col):
    data = []
    for (uri, rank, rankee) in rank_array(df, df_col):
        data.append([uri, rank, rankee])
    ranked_df = pd.DataFrame(data, columns=["uri", "rank", rank_col])
    return ranked_df


def createIdsFromTag(tag_df, tag):
    id_df = pd.DataFrame()
    id_df[tag] = tag_df[tag].unique()
    id_df[tag + "Id"] = range(1, len(id_df) + 1)
    id_df = id_df[[tag + "Id", tag]]

    tagToId = {
        tag: id for (tag, id) in zip(id_df[tag], id_df[tag + "Id"])
    }

    tag_df[tag + "Id"] = tag_df[tag].map(tagToId)
    return id_df


fileRead = f"./data/NYT_Data_Clean_{startMonth}_{startYear}_to_{endMonth}_{endYear}.parquet"

print("Reading " + fileRead)
article_df = pd.read_parquet(fileRead)
article_df["pub_date"] = pd.to_datetime(article_df["pub_date"])
article_df["articleId"] = range(1, len(article_df) + 1)

person_tag_df = rank_df(article_df, "people", "person")
organization_tag_df = rank_df(article_df, "organizations", "organization")
subject_tag_df = rank_df(article_df, "subjects", "subject")
location_tag_df = rank_df(article_df, "locations", "location")

articleUriToId = {
    uri: id for (uri, id) in zip(article_df["uri"], article_df["articleId"])
}

article_df = article_df[["articleId", "pub_date", "pub_year", "main_headline",
                         "lead_paragraph", "web_url"]]

tag_df_tables = [(person_tag_df, "person_tag"), (organization_tag_df,
                                                 "organization_tag"), (subject_tag_df, "subject_tag"), (location_tag_df, "location_tag")]
for df, df_col in tag_df_tables:
    df["articleId"] = df["uri"].map(articleUriToId)

person_df = createIdsFromTag(person_tag_df, "person")
organization_df = createIdsFromTag(organization_tag_df, "organization")
subject_df = createIdsFromTag(subject_tag_df, "subject")
location_df = createIdsFromTag(location_tag_df, "location")

person_tag_df = person_tag_df[["articleId", "rank", "personId"]]
organization_tag_df = organization_tag_df[[
    "articleId", "rank", "organizationId"]]
subject_tag_df = subject_tag_df[[
    "articleId", "rank", "subjectId"]]
location_tag_df = location_tag_df[[
    "articleId", "rank", "locationId"]]

print(article_df)
print(person_df)
print(person_tag_df)
print(organization_tag_df)
print(subject_tag_df)
print(location_tag_df)

df_tables = [(article_df, "article"), (person_df, "person"), (organization_df,
                                                              "organization"), (subject_df, "subject"), (location_df, "location")]

tag_df_tables = [(person_tag_df, "person_tag"), (organization_tag_df,
                                                 "organization_tag"), (subject_tag_df, "subject_tag"), (location_tag_df, "location_tag")]

print("Table Updates Generated")

print("Connecting to Database")
load_dotenv()
database_engine = os.getenv("SQL_ENGINE")
engine = sa.create_engine(
    database_engine, encoding="utf-8", poolclass=SingletonThreadPool, echo=True)

with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
    print("Connected to Database")
    metadata = sa.MetaData()
    metadata.reflect(bind=engine)

    with connection.begin():
        print("Truncating Tables")
        connection.execute("SET SESSION FOREIGN_KEY_CHECKS = OFF")
        for table in metadata.sorted_tables:
            connection.execute(table.delete())

    print("Updating Tables")

    for df, table in df_tables:
        df.to_sql(table, connection, if_exists="append",
                  index=False, chunksize=1000, method="multi")

    print("Updating Tags")

    for tag_df, tag_table in tag_df_tables:
        tag_df.to_sql(tag_table, connection, if_exists="append",
                      index=False, chunksize=1000, method="multi")

    connection.close()
engine.dispose()

print("Finished Updating")
