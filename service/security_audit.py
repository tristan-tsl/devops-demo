import json

from bson.json_util import dumps
from flask import Blueprint, request

from component.my_mongo import mongodb

app = Blueprint('security_audit', __name__, url_prefix='/security_audit')

login_user_operate_log_co = mongodb['login_user_operate_log']


@app.route('/query', methods=['POST'])
def query():
    my_filter = {}
    search_condition = []
    page_size = 9999999
    page_no = 1
    try:
        request_data = request.get_data()
        request_data = json.loads(request_data)
        search = request_data["search"]
        user_id = search["user_id"]
        if user_id:
            search_condition.append({"user_id": user_id})
        # # 分页
        page = request_data["page"]
        if page["current"]:
            page_no = page["current"]
        if page["page_size"]:
            page_size = page["page_size"]
    except Exception as e:
        print(e)
    skip = page_size * (page_no - 1)
    if len(search_condition) > 0:
        my_filter = {"$and": search_condition}
    return dumps(
        {"data": login_user_operate_log_co.find(filter=my_filter, sort=[("_id", -1)]).limit(
            page_size).skip(skip),
         "total": login_user_operate_log_co.find(filter=my_filter, sort=[("_id", -1)]).limit(
             page_size).skip(skip).count()})
