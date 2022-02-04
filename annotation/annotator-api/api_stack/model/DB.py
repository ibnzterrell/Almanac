from flask import g
import os
import sqlalchemy as sa
import pandas as pd

def db_connect():
    engine = getattr(g, '_engine', None)
    articleTable = getattr(g, '_articleTable', None)
    personTable = getattr(g, '_personTable', None)
    personTagTable = getattr(g, '_personTagTable', None)
    organizationTable = getattr(g, '_organizationTable', None)
    organizationTagTable = getattr(g, '_organizationTagTable', None)

    if engine is None:
        engine = g._engine = sa.create_engine(
            os.getenv("SQL_ENGINE"), echo=True)

    if articleTable is None:
        md = sa.MetaData()
        md.reflect(bind=engine)
        articleTable = g.__articleTable = md.tables["article"]

    if personTable is None:
        personTable = g.__personTable = md.tables["person"]

    if personTagTable is None:
        personTagTable = g.__personTagTable = md.tables["person_tag"]

    if organizationTable is None:
        organizationTable = g.__organizationTable = md.tables["organization"]

    if organizationTagTable is None:
        organizationTagTable = g.__organizationTagTable = md.tables["organization_tag"]

    db = engine.connect()

    return (db, articleTable, personTable, personTagTable, organizationTable, organizationTagTable)

def db_disconnect():
    engine = getattr(g, '_engine', None)
    if engine is not None:
        engine.dispose()
        g._engine = None

def personEventQuery(name):
    (db_conn, articleTable, personTable, personTagTable, organizationTable, organizationTagTable) = db_connect()

    joinPersonTag = sa.sql.join(
        personTable, personTagTable, personTable.c.personId == personTagTable.c.personId)

    joinPersonTagArticle = sa.sql.join(
        articleTable, joinPersonTag, articleTable.c.articleId == personTagTable.c.articleId)

    # Tags are ordered by relevance, only select articles where they are first or second person listed
    sqlQuery = sa.sql.select([articleTable.c.main_headline,
                              articleTable.c.pub_date, articleTable.c.lead_paragraph, articleTable.c.abstract, articleTable.c.web_url]).select_from(joinPersonTagArticle).where(personTable.c.person == name).where(personTagTable.c.rank <= 2)

    df = pd.read_sql_query(sql=sqlQuery, con=db_conn)
    db_conn.close()

    return df

def topicEventQuery(topic):
    (db_conn, articleTable, personTable, personTagTable, organizationTable, organizationTagTable) = db_connect()

       # Tags are ordered by relevance, only select articles where they are first person listed
    sqlQuery = sa.sql.select([articleTable.c.main_headline, articleTable.c.pub_date, articleTable.c.lead_paragraph, articleTable.c.abstract, articleTable.c.web_url]).where(
        articleTable.c.subjects.ilike(f"[\'{topic}%"))

    df = pd.read_sql_query(sql=sqlQuery, con=db_conn)
    db_conn.close()

    return df

def textEventQuery(text):
    (db_conn, articleTable, personTable, personTagTable, organizationTable, organizationTagTable) = db_connect()

    # Hack since SQLALchemy still doesn't support natural language mode ¯\_(ツ)_/¯
    sqlQuery = sa.text("SELECT article.main_headline, article.pub_date, article.lead_paragraph, article.abstract, article.web_url,  MATCH (article.main_headline, article.lead_paragraph) AGAINST ((:textSearch) IN NATURAL LANGUAGE MODE) AS relevance FROM article WHERE MATCH (article.main_headline, article.lead_paragraph) AGAINST ((:textSearch) IN NATURAL LANGUAGE MODE)")
    # NOTE: We bind parameters separately to prevent SQL injections
    sqlQuery = sqlQuery.bindparams(textSearch=text)

    df = pd.read_sql_query(sql=sqlQuery, con=db_conn)
    db_conn.close()

    return df

def orgEventQuery(org):
    (db_conn, articleTable, personTable, personTagTable, organizationTable, organizationTagTable) = db_connect()

    joinOrgTag = sa.sql.join(
        organizationTable, organizationTagTable, organizationTable.c.organizationId == organizationTagTable.c.organizationId)

    joinOrgTagArticle = sa.sql.join(
        joinOrgTag, articleTable, organizationTagTable.c.articleId == articleTable.c.articleId)

    # Tags are ordered by relevance, only select articles where they are first or second person listed
    sqlQuery = sa.sql.select([articleTable.c.main_headline,
                              articleTable.c.pub_date, articleTable.c.lead_paragraph, articleTable.c.abstract, articleTable.c.web_url]).select_from(joinOrgTagArticle).where(organizationTable.c.organization == org).where(organizationTagTable.c.rank <= 1)

    df = pd.read_sql_query(sql=sqlQuery, con=db_conn)
    db_conn.close()

    return df

def personQuery(name):
    (db_conn, articleTable, personTable, personTagTable, organizationTable, organizationTagTable) = db_connect()

    joinPersonTag = sa.sql.join(personTable, personTagTable, personTable.c.personId == personTagTable.c.personId)

    sqlQuery = sa.sql.select([personTable.c.person, sa.func.count().label("articleCount")]).select_from(joinPersonTag).where(personTable.c.person.like(f"{name}%")).group_by(personTable.c.person).order_by(sa.desc("articleCount"))
    df = pd.read_sql_query(sql=sqlQuery, con=db_conn)
    db_conn.close()

    return df

def topicQuery(topic):
    (db_conn, articleTable, personTable, personTagTable, organizationTable, organizationTagTable) = db_connect()

    sqlQuery = sa.sql.select([personTable.c.person]).select_from(personTable).where(personTable.c.person.ilike(f"{topic}%"))
    df = pd.read_sql_query(sql=sqlQuery, con=db_conn)
    db_conn.close()

    return df

def orgQuery(org):
    (db_conn, articleTable, personTable, personTagTable, organizationTable, organizationTagTable) = db_connect()
    
    joinOrgTag = sa.sql.join(organizationTable, organizationTagTable, organizationTable.c.organizationId == organizationTagTable.c.organizationId)

    sqlQuery = sa.sql.select([organizationTable.c.organization, sa.func.count().label("articleCount")]).select_from(joinOrgTag).where(organizationTable.c.organization.like(f"{org}%")).group_by(organizationTable.c.organization).order_by(sa.desc("articleCount"))
    df = pd.read_sql_query(sql=sqlQuery, con=db_conn)
    db_conn.close()

    return df