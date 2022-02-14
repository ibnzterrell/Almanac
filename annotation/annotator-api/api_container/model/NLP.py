import spacy

def loadNLP():
    nlp = spacy.load("en_core_web_sm", exclude=["ner"])
    return nlp

def wordFilter(token, alphaFilter: bool):
    if (alphaFilter):
        return token.is_alpha and not token.is_stop
    return ((not token.is_punct) and (not token.is_stop))