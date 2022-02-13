from flask import Blueprint, request, make_response
from services.headline_service import headline_query, headline_cluster_query
import json

headlineAPI = Blueprint("headline_route", __name__)

@headlineAPI.route("/headline", methods=["POST"])
def headline_route():
    req_data = json.loads(request.data)
    #print(req_data)
    res_data = headline_query(req_data)
    #print(res_data)
    return make_response(res_data, 200)

@headlineAPI.route("/cluster", methods=["POST"])
def cluster_route():
    req_data = json.loads(request.data)
    #print(req_data)
    res_data = headline_cluster_query(req_data)
    #print(res_data)
    return make_response(res_data, 200)