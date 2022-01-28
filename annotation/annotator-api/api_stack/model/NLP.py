from flask import g
import spacy

def loadNLP():
    nlp = getattr(g, '_nlp', None)
    if nlp is None:
        nlp = spacy.load("en_core_web_sm", exclude=["ner"])
        g._nlp = nlp
    return nlp
