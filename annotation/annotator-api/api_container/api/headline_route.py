from fastapi import APIRouter, Request
from model.DB import db_connect
from model.APIOptions import Granularity
from services.headline_service import headline_query

headlineAPI = APIRouter()

@headlineAPI.post("/headline")
async def headline_route(request: Request, 
        granularity: Granularity,
        dateField: str,
        query: str,
        alphaFilter: bool = False,
        decayWeighting: bool = False,
        alternates: bool = False,
        topK: bool = False
    ):
    db = db_connect(request.app.state.engine)
    #print(req_data)
    data = (await request.json())["data"]

    options = dict(
        alphaFilter = alphaFilter,
        decayWeighting = decayWeighting,
        alternates = alternates,
        topK = topK
    )

    res_data = headline_query(db, data, granularity, dateField, query, options)

    return res_data