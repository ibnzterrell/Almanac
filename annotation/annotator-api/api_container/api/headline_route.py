from fastapi import APIRouter, Request
from model.DB import db_connect
from model.Options import Granularity, HeadlineSearch, WordConsolidation
from services.headline_service import headline_query

headlineAPI = APIRouter()


@headlineAPI.post("/headline")
async def headline_route(request: Request):
    db = db_connect(request.app.state.engine)
    pipelines = request.app.state.pipelines
    req = await request.json()
    data = req["data"]
    params = req["params"]
    options = req["options"]

    res_data = headline_query(db, pipelines, data, params, options)

    return res_data
