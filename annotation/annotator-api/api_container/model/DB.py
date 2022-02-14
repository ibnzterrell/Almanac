import os
import sqlalchemy as sa
import pandas as pd

def db_startup():
    engine = sa.create_engine(
            os.getenv("SQL_ENGINE"), echo=True)
    return engine

def db_connect(engine):
    md = sa.MetaData()
    
    db_conn = engine.connect()
    md.reflect(bind=db_conn)

    return (db_conn, md)

def db_shutdown(engine):
    engine.dispose()

def personEventQuery(db, name):
    (db_conn, md) = db

    articleTable = md.tables["article"]
    personTable = md.tables["person"]
    personTagTable = md.tables["person_tag"]

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

def topicEventQuery(db, topic):
    (db_conn, md) = db

    articleTable = md.tables["article"]

       # Tags are ordered by relevance, only select articles where they are first person listed
    sqlQuery = sa.sql.select([articleTable.c.main_headline, articleTable.c.pub_date, articleTable.c.lead_paragraph, articleTable.c.abstract, articleTable.c.web_url]).where(
        articleTable.c.subjects.ilike(f"[\'{topic}%"))

    df = pd.read_sql_query(sql=sqlQuery, con=db_conn)
    db_conn.close()

    return df

def textEventQuery(db, text):
    (db_conn, md) = db

    # Hack since SQLALchemy still doesn't support natural language mode ¯\_(ツ)_/¯
    sqlQuery = sa.text("SELECT article.main_headline, article.pub_date, article.lead_paragraph, article.abstract, article.web_url,  MATCH (article.main_headline, article.lead_paragraph) AGAINST ((:textSearch) IN NATURAL LANGUAGE MODE) AS relevance FROM article WHERE MATCH (article.main_headline, article.lead_paragraph) AGAINST ((:textSearch) IN NATURAL LANGUAGE MODE)")
    # NOTE: We bind parameters separately to prevent SQL injections
    sqlQuery = sqlQuery.bindparams(textSearch=text)

    df = pd.read_sql_query(sql=sqlQuery, con=db_conn)
    db_conn.close()

    return df

def orgEventQuery(db, org):
    (db_conn, md) = db

    articleTable = md.tables["article"]
    organizationTable = md.tables["organization"]
    organizationTagTable = md.tables["organization_tag"]

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

def personQuery(db, name):
    (db_conn, md) = db

    personTable = md.tables["person"]
    personTagTable = md.tables["person_tag"]

    joinPersonTag = sa.sql.join(personTable, personTagTable, personTable.c.personId == personTagTable.c.personId)

    sqlQuery = sa.sql.select([personTable.c.person, sa.func.count().label("articleCount")]).select_from(joinPersonTag).where(personTable.c.person.like(f"{name}%")).group_by(personTable.c.person).order_by(sa.desc("articleCount"))
    df = pd.read_sql_query(sql=sqlQuery, con=db_conn)
    db_conn.close()

    return df

def topicQuery(db, topic):
    (db_conn, md) = db

    personTable = md.tables["person"]

    sqlQuery = sa.sql.select([personTable.c.person]).select_from(personTable).where(personTable.c.person.ilike(f"{topic}%"))
    df = pd.read_sql_query(sql=sqlQuery, con=db_conn)
    db_conn.close()

    return df

def orgQuery(db, org):
    (db_conn, md) = db
    
    organizationTable = md.tables["organization"]
    organizationTagTable = md.tables["organization_tag"]

    joinOrgTag = sa.sql.join(organizationTable, organizationTagTable, organizationTable.c.organizationId == organizationTagTable.c.organizationId)

    sqlQuery = sa.sql.select([organizationTable.c.organization, sa.func.count().label("articleCount")]).select_from(joinOrgTag).where(organizationTable.c.organization.like(f"{org}%")).group_by(organizationTable.c.organization).order_by(sa.desc("articleCount"))
    df = pd.read_sql_query(sql=sqlQuery, con=db_conn)
    db_conn.close()

    return df