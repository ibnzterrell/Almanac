from flask import Blueprint, request, make_response
from services.search_service import search_query

searchAPI = Blueprint("search_route", __name__)

@searchAPI.route("/search/<tagType>/<query>", methods=["GET"])
def search_route(tagType, query):
    res_data = search_query(tagType, query)
    print(res_data)
    return make_response(res_data, 200)
