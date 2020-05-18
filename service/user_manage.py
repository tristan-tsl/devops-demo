import json

from bson.json_util import dumps
from flask import Blueprint, request

from component.my_mongo import mongodb

app = Blueprint('user_manage', __name__, url_prefix='/user_manage')

dingding_user_info_co = mongodb['dingding_user_info']


@app.route('/users', methods=['GET'])
def get_users():
    return dumps(dingding_user_info_co.find({}, {"_id": 0, "openid": 1, "nick": 1}))


def wrap_user_dingding_info():
    users = json.loads(get_users())
    users_obj = {}
    for user in users:
        users_obj[user["openid"]] = user["nick"]

    return users_obj


def get_user_nick_by_dingding_open_id(open_id):
    return wrap_user_dingding_info()[open_id]


@app.route('/get_nick_by_open_id', methods=['POST'])
def get_nick_by_open_id():
    request_data = request.get_data()
    request_data = json.loads(request_data)
    openid = request_data["openid"]
    return get_user_nick_by_dingding_open_id(openid)


def get_cur_ding_id(user_id):
    dingding_user_info_co_old = dingding_user_info_co.find_one({"openid": user_id})
    if not dingding_user_info_co_old.__contains__("dingId"):
        return None
    ding_id = dingding_user_info_co_old["dingId"]
    return ding_id
