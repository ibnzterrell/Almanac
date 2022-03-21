import spacy
from nltk.stem import WordNetLemmatizer
from nltk.stem.porter import PorterStemmer
from nltk.stem.lancaster import LancasterStemmer
from model.Options import WordConsolidation

def wordFilter(token, alphaFilter: bool):
    if (alphaFilter):
        return token.is_alpha and not token.is_stop
    return ((not token.is_punct) and (not token.is_stop))

WordNet = WordNetLemmatizer()
porter = PorterStemmer()
lancaster = LancasterStemmer()

@spacy.Language.component("lemmatizer-WordNet")
def lemmatizerWordNet(doc):
    for token in doc:
        token.lemma_ = WordNet.lemmatize(token.text)

    return doc

@spacy.Language.component("stemmer-porter")
def stemmerPorter(doc):
    for token in doc:
        token.lemma_ = porter.stem(token.text)

    return doc

@spacy.Language.component("stemmer-lancaster")
def stemmerLancaster(doc):
    for token in doc:
        token.lemma_ = lancaster.stem(token.text)

    return doc

def loadNLP():
    pipelines = {}
    pipelines[WordConsolidation.lemma_spaCy_sm] = spacy.load("en_core_web_sm", exclude=["ner"])
    # pipes[WordConsolidation.lemma_spaCy_md] = spacy.load("en_core_web_md", exclude=["ner"])
    # pipes[WordConsolidation.lemma_spaCy_lg] = spacy.load("en_core_web_lg", exclude=["ner"])
    # pipes[WordConsolidation.lemma_RoBERTa] = spacy.load("en_core_web_trf", exclude=["ner"])
    lemma_WordNetPipeline = spacy.load("en_core_web_sm", exclude=["lemmatizer", "ner"])
    lemma_WordNetPipeline.add_pipe("lemmatizer-WordNet")
    pipelines[WordConsolidation.lemma_WordNet] = lemma_WordNetPipeline

    stem_PorterPipeline = spacy.load("en_core_web_sm", exclude=["lemmatizer", "ner"])
    stem_PorterPipeline.add_pipe("stemmer-porter")
    pipelines[WordConsolidation.stem_porter] = stem_PorterPipeline

    stem_LancasterPipeline = spacy.load("en_core_web_sm", exclude=["lemmatizer", "ner"])
    stem_LancasterPipeline.add_pipe("stemmer-lancaster")
    pipelines[WordConsolidation.stem_lancaster] = stem_LancasterPipeline

    return pipelines

def getNLP(pipelines, options):
    return pipelines[options["consolidationMethod"]]