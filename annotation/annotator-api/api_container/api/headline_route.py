from fastapi import APIRouter, Request
from model.DB import db_connect
from model.Options import Granularity, HeadlineSearch, WordConsolidation
from services.headline_service import headline_point_query, headline_range_query

headlineAPI = APIRouter()


@headlineAPI.post("/headline/point")
async def headline_point_route(request: Request):
    db = db_connect(request.app.state.engine)
    pipelines = request.app.state.pipelines
    req = await request.json()
    data = req["data"]
    params = req["params"]
    options = req["options"]

    res_data = headline_point_query(db, pipelines, data, params, options)

    return res_data


@headlineAPI.post("/headline/range")
async def headline_range_route(request: Request):
    db = db_connect(request.app.state.engine)
    pipelines = request.app.state.pipelines
    req = await request.json()
    ranges = req["ranges"]
    params = req["params"]
    options = req["options"]

    res_data = headline_range_query(db, pipelines, ranges, params, options)

    return res_data
