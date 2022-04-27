from model.DB import personQuery, topicQuery, orgQuery, textEventQuery
import json

def findPerson(db, name):
    return personQuery(db, name)

def findTopic(db, topic):
    return topicQuery(db, topic)

def findOrg(db, org):
    return orgQuery(db, org)

def findTextHeadline(db, text):
    options = {
        "querySpace": "headline",
        "queryMode": "boolean"
    }
    return textEventQuery(db, text, options)

def findTextHeadlineWithLead(db, text):
    options = {
        "querySpace": "headlinewithlead",
        "queryMode": "boolean"
    }
    return textEventQuery(db, text, options)

tagTypeToFind = {
    "person": findPerson,
    "topic": findTopic,
    "org": findOrg,
    "headline": findTextHeadline,
    "headlinewithlead": findTextHeadlineWithLead
}

def search_query(db, tagType, query):
    findTag = tagTypeToFind[tagType]
    res_data = findTag(db, query).to_json(orient='records')
    res_data = json.loads(res_data)
    return res_data