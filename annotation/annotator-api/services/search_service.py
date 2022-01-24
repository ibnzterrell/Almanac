import pandas as pd
import json
from model.DB import personQuery, topicQuery, orgQuery

def findPerson(name):
    return personQuery(name)

def findTopic(topic):
    return topicQuery(topic)

def findOrg(org):
    return orgQuery(org)

tagTypeToFind = {
    "person": findPerson,
    "topic": findTopic,
    "org": findOrg 
}

def search_query(tagType, query):
    findTag = tagTypeToFind[tagType]
    res_data = findTag(query).to_json(orient='records')
    
    return res_data