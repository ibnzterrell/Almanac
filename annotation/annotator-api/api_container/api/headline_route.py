from fastapi import APIRouter, Request
from model.DB import db_connect
from model.DataFrameContainer import DataFrameContainer
from model.APIOptions import Granularity
from services.headline_service import headline_query

headlineAPI = APIRouter()

@headlineAPI.post("/headline")
async def headline_route(request: Request, 
        granularity: Granularity,
        dateField: str,
        query: str
    ):
    db = db_connect(request.app.state.engine)
    #print(req_data)
    data = (await request.json())["data"]
    res_data = headline_query(db, data, granularity, dateField, query)
    #print(res_data)
    return res_data