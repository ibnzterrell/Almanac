import json
import pandas as pd
from flask import Flask, request, g
from flask_cors import CORS, cross_origin
import sqlalchemy as sa
import re
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
CORS(app)

def db_connect():
    db = getattr(g, '_database', None)
    articleTable = getattr(g, '_articleTable', None)
    personTable = getattr(g, '_personTable', None)
    personTagTable = getattr(g, '_personTagTable', None)
    engine = getattr(g, '_engine', None)

    if engine is None:
        engine = g._engine = sa.create_engine(
            os.getenv("SQL_ENGINE"), echo=True)
    
    if db is None:
        db = g._database = engine.connect()

    if articleTable is None:
        md = sa.MetaData()
        md.reflect(bind=engine)
        articleTable = g.__articleTable = md.tables["article"]

    if personTable is None:
        personTable = g.__personTable = md.tables["person"]

    if personTagTable is None:
        personTagTable = g.__personTagTable = md.tables["person_tag"]

    return (db, articleTable, personTable, personTagTable)


def legalize(name):
    # Convert common name to legal name for NYT lookup
    return {
        "joe biden": "Joseph R Jr Biden",
        "bernie sanders": "Bernard Sanders",
        "jack welch": "John F Jr Welch"
    }.get(name, name)  # Return name if not found


def convertNameForNYT(name):
    name = legalize(name)

    # Convert name from Cable TV format (first middle last) to NYT format (last, first middle)
    results = re.search("(.*) (.*)", name).groups()

    # Certain names from the NYT do not use comma notation (Chinese mostly)
    if name in ["xi jinping"]:
        return name

    return f"{results[1]}, {results[0]}"


def findPersonEvents(name, events, dateField):
    # name = convertNameForNYT(name)
    df = []

    (db_conn, articleTable, personTable, personTagTable) = db_connect()

    # Tags are ordered by relevance, only select articles where they are first person listed
    # sqlQuery = sa.sql.select([articlesTable.c.main_headline, articlesTable.c.pub_date]).where(
    #     articlesTable.c.person1.ilike(f"%{name}%"))

    joinTagPerson = sa.sql.join(
        personTagTable, personTable, personTagTable.c.personId == personTable.c.personId)

    joinArticleTagPerson = sa.sql.join(
        articleTable, joinTagPerson, articleTable.c.articleId == personTagTable.c.articleId)

    sqlQuery = sa.sql.select([articleTable.c.main_headline,
                              articleTable.c.pub_date]).select_from(joinArticleTagPerson).where(personTable.c.person == name)

    df = pd.read_sql_query(sql=sqlQuery, con=db_conn)
    return findEvents(df, events, dateField)


def findTopicEvents(topic, events, dateField):
    df = []

    (db_conn, articlesTable) = db_connect()

    # Tags are ordered by relevance, only select articles where they are first person listed
    sqlQuery = sa.sql.select([articlesTable.c.main_headline, articlesTable.c.pub_date]).where(
        articlesTable.c.subjects.ilike(f"[\'{topic}%"))
    # NOTE While fairly limiting, we use SQLAlchemy selectables instead of raw queries to prevent SQL injection

    # TODO Make more efficient by doing processing ahead of time to offload date filtering to DB
    # TODO Make more accurate using Heideltime NLP to temporalize events
    df = pd.read_sql_query(sql=sqlQuery, con=db_conn)
    return findEvents(df, events, dateField)


def findTextEvents(text, events, dateField):
    df = []

    (db_conn, articlesTable) = db_connect()

    # Tags are ordered by relevance, only select articles where they are first person listed

    sqlQuery = sa.sql.select([articlesTable.c.main_headline, articlesTable.c.pub_date]).where(
        articlesTable.c.main_headline.ilike(f"%{text}%"))

    # TODO Make more efficient by doing processing ahead of time to offload date filtering to DB
    # TODO Make more accurate using Heideltime NLP to temporalize events
    df = pd.read_sql_query(sql=sqlQuery, con=db_conn)
    return findEvents(df, events, dateField)


def findOrgEvents(org, events, dateField):
    df = []

    (db_conn, articlesTable) = db_connect()

    # Tags are ordered by relevance, only select articles where they are first person listed
    sqlQuery = sa.sql.select([articlesTable.c.main_headline, articlesTable.c.pub_date]).where(
        articlesTable.c.organizations.ilike(f"[\'{org}%"))

    # TODO Make more efficient by doing processing ahead of time to offload date filtering to DB
    # TODO Make more accurate using Heideltime NLP to temporalize events
    df = pd.read_sql_query(sql=sqlQuery, con=db_conn)
    return findEvents(df, events, dateField)


def findEvents(df, events, dateField):
    # Cut ISO dates to year-month e.g. 2020-11 for string-based date matching
    print(df['pub_date'])
    df['month_date'] = pd.to_datetime(df['pub_date']).dt.to_period('M')
    # NOTE efficient but not as accurate
    events["month_date"] = pd.to_datetime(events[dateField]).dt.to_period('M')
    print(df['month_date'])
    print(events["month_date"])
    df = df[df["month_date"].isin(events["month_date"])]

    # If multiple articles keep most recent one - most likely to have most information
    # NOTE NLP temporal / volume-based event detection should help with which article to use later on
    df = df.drop_duplicates(subset=["month_date"], keep="last")
    df["annotation"] = df["main_headline"]
    # df["date"] = df["pub_date"]
    df = df[["pub_date", "month_date", "annotation"]]
    print(df.dtypes)
    print(events.dtypes)
    df = pd.merge(df, events, on="month_date")
    df = df.drop(columns=["month_date"])
    return df


@app.route("/headlines", methods=["POST"])
def eventsRoute():
    data = json.loads(request.data)
    print(data)
    events = pd.DataFrame.from_records(data["data"])
    dateField = data["date"]

    df = pd.DataFrame()
    if (data["method"] == "person"):
        df = findPersonEvents(data["tag"], events, dateField)
    elif (data["method"] == "topic"):
        df = findTopicEvents(data["tag"], events, dateField)
    elif (data["method"] == "text"):
        df = findTextEvents(data["tag"], events, dateField)
    elif (data["method"] == "org"):
        df = findOrgEvents(data["tag"], events, dateField)

    return df.to_json(orient='records')


@app.route("/warmup", methods=["GET"])
def warmupRoute(name):
    db_connect()
    return "OK"

# Close database on shutdown
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


if __name__ == '__main__':
    app.run(port=3030)
