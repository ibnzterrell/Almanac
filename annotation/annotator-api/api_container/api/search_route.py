from fastapi import APIRouter, Request
from services.search_service import search_query
from model.DB import db_connect

searchAPI = APIRouter()

@searchAPI.get("/search/{tagType}/{query}")
async def search_route(request: Request, tagType: str, query: str):
    db = db_connect(request.app.state.engine)
    res_data = search_query(db, tagType, query)
    #print(res_data)
    return res_data
