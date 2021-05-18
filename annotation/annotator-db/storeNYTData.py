import pandas as pd
import json
from sqlalchemy import create_engine


def rank_array(df, column):
    for uri, arr in zip(df["uri"], df[column]):
        arr = json.loads(arr)
        for i, a in enumerate(arr):
            rank = i + 1
            yield(uri, rank, a)


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

fileRead = "./data/NYT_Data_Raw_1_2000_to_5_2021.csv"
print("Reading " + fileRead)
article_df = pd.read_csv(fileRead)
article_df["pub_date"] = pd.to_datetime(article_df["pub_date"])
article_df["articleId"] = range(1, len(article_df) + 1)

engine = create_engine(
    "[ENGINE]", echo=True)
sql_connection = engine.connect()

person_tag_df = rank_df(article_df, "people", "person")
organization_tag_df = rank_df(article_df, "organizations", "organization")
subject_tag_df = rank_df(article_df, "subjects", "subject")
location_tag_df = rank_df(article_df, "locations", "location")

articleUriToId = {
    uri: id for (uri, id) in zip(article_df["uri"], article_df["articleId"])
}

article_df = article_df[["articleId", "pub_date", "main_headline",
                         "web_url", "abstract", "lead_paragraph", "print_headline"]]

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

print("Updating Tables")

df_tables = [(article_df, "article"), (person_df, "person"), (organization_df,
                                                              "organization"), (subject_df, "subject"), (location_df, "location")]

tag_df_tables = [(person_tag_df, "person_tag"), (organization_tag_df,
                                                 "organization_tag"), (subject_tag_df, "subject_tag"), (location_tag_df, "location_tag")]
for df, table in df_tables:
    df.to_sql(table, sql_connection, if_exists="replace",
              index=False, chunksize=1000)

for tag_df, tag_table in tag_df_tables:
    tag_df.to_sql(tag_table, sql_connection, if_exists="replace",
                  index=False, chunksize=1000)

print("Finished Updating Tables")
sql_connection.close()
