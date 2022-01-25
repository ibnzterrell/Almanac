from flask import g
import spacy


# def loadNLP():
#     nlp = getattr(g, '_nlp', None)
#     if nlp is None:
#         nlp = spacy.load("/opt/en_core_web_sm-2.2.5/en_core_web_sm/en_core_web_sm-2.2.5")
#         g._nlp = nlp
#     return nlp


def loadNLP():
    nlp = getattr(g, '_nlp', None)
    if nlp is None:
        nlp = spacy.load("en_core_web_sm")
        g._nlp = nlp
    return nlp
