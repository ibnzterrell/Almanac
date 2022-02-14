from model.DB import personQuery, topicQuery, orgQuery

def findPerson(db, name):
    return personQuery(db, name)

def findTopic(db, topic):
    return topicQuery(db, topic)

def findOrg(db, org):
    return orgQuery(db, org)

tagTypeToFind = {
    "person": findPerson,
    "topic": findTopic,
    "org": findOrg 
}

def search_query(db, tagType, query):
    findTag = tagTypeToFind[tagType]
    res_data = findTag(db, query).to_json(orient='records')
    
    return res_data