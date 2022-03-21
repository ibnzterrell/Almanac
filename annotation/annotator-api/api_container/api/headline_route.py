from fastapi import APIRouter, Request
from model.DB import db_connect
from model.Options import Granularity, HeadlineSearch, WordConsolidation
from services.headline_service import headline_query

headlineAPI = APIRouter()

@headlineAPI.post("/headline")
async def headline_route(request: Request, 
        granularity: Granularity,
        dateField: str,
        query: str,
        querySpace: HeadlineSearch = HeadlineSearch.headlinewithlead,
        scoringSpace: HeadlineSearch = HeadlineSearch.headline,
        consolidationMethod: WordConsolidation = WordConsolidation.lemma_spaCy_lg,
        alphaFilter: bool = False,
        decayWeighting: bool = False,
        alternates: bool = False,
        topK: bool = False,
        singleDocumentFilter: bool = False,
        booleanFrequencies: bool = False
    ):
    db = db_connect(request.app.state.engine)
    pipes = request.app.state.pipes
    data = (await request.json())["data"]

    options = dict(
        alphaFilter = alphaFilter,
        decayWeighting = decayWeighting,
        alternates = alternates,
        topK = topK,
        querySpace = querySpace,
        scoringSpace = scoringSpace,
        consolidationMethod = consolidationMethod,
        singleDocumentFilter = singleDocumentFilter,
        booleanFrequencies = booleanFrequencies
    )

    res_data = headline_query(db, pipes, data, granularity, dateField, query, options)

    return res_data