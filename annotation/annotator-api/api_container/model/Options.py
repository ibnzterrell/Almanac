from enum import Enum

class Granularity(str, Enum):
    day = "day"
    week = "week"
    month = "month"

class HeadlineSearch(str, Enum):
    headline = "headline"
    headlinewithlead = "headlinewithlead"

class WordConsolidation(str, Enum):
    lemma_spaCy_sm = "lemma_spaCy_sm"
    lemma_spaCy_md = "lemma_spaCy_md"
    lemma_spaCy_lg = "lemma_spaCy_lg"
    lemma_RoBERTa = "lemma_RoBERTa"
    lemma_WordNet = "lemma_WordNet"
    stem_porter = "stem_porter"
    stem_lancaster = "stem_lancaster"
    stem_snowball = "stem_snowball"