from fastapi import APIRouter, Request
from model.DB import db_connect
from model.OptionsValidation import Granularity, HeadlineSearchSpace
from services.headline_service import headline_query

headlineAPI = APIRouter()

@headlineAPI.post("/headline")
async def headline_route(request: Request, 
        granularity: Granularity,
        dateField: str,
        query: str,
        querySpace: HeadlineSearchSpace = HeadlineSearchSpace.headlinewithlead,
        scoringSpace: HeadlineSearchSpace = HeadlineSearchSpace.headline,
        alphaFilter: bool = False,
        decayWeighting: bool = False,
        alternates: bool = False,
        topK: bool = False
    ):
    db = db_connect(request.app.state.engine)
    data = (await request.json())["data"]

    options = dict(
        alphaFilter = alphaFilter,
        decayWeighting = decayWeighting,
        alternates = alternates,
        topK = topK,
        querySpace = querySpace.value,
        scoringSpace = scoringSpace.value
    )

    res_data = headline_query(db, data, granularity, dateField, query, options)

    return res_data