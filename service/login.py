import datetime
import json

import requests
from flask import Blueprint, request

from component import my_dingding
from component.my_mongo import mongodb
from config import app_conf

app = Blueprint('login', __name__, url_prefix='/login')

dingding_co = mongodb['dingding']
dingding_user_info_co = mongodb['dingding_user_info']
dingding_login_record_co = mongodb['dingding_login_record']
if not dingding_co.find_one():
    dingding_co.insert_one({})


@app.route('/dingding', methods=['GET'])
def dingding():
    code = request.args.get("code")
    # 获取access_token
    dingding_co_one = dingding_co.find_one()
    if dingding_co_one:
        access_token = dingding_co_one["access_token"]
    # 获取用户授权的持久授权码
    persistent_code_dict = my_dingding.get_persistent_code(code, access_token)
    openid = persistent_code_dict["openid"]
    persistent_code = persistent_code_dict["persistent_code"]
    # 获取sns_token
    sns_token = my_dingding.get_sns_token(openid, persistent_code, access_token)
    # 获取用户信息
    user_info = my_dingding.get_user_info(sns_token)
    user_info_detail = user_info["user_info"]
    openid = user_info_detail["openid"]
    nick = user_info_detail["nick"]
    dingId = user_info_detail["dingId"]
    cur_date = datetime.datetime.now().strftime('%Y.%m.%d-%H:%M:%S')
    # 明确思路
    # 后端将 openid:nick code:openid 存起来 查询存在则修改 不存在则新增
    dingding_user_info_co_old = dingding_user_info_co.find_one({"openid": openid})
    dingding_user_info_co_new = {
        "openid": openid,
        "nick": nick,
        "dingId": dingId,
        "last_update_date": cur_date}
    if dingding_user_info_co_old:
        dingding_user_info_co.update_one({}, {
            '$set': dingding_user_info_co_new})
    else:
        dingding_user_info_co.insert_one(dingding_user_info_co_new)

    dingding_login_record_co_old = dingding_login_record_co.find_one({"openid": openid})

    if dingding_login_record_co_old:
        update_result = dingding_login_record_co.update_one(filter={"openid": openid},
                                                            update={
                                                                '$set': {"last_update_date": cur_date, "code": code}})
        print("update_result", update_result)
    else:
        dingding_login_record_co_new = {
            "openid": openid,
            "code": code,
            "nick": nick,
            "last_update_date": cur_date}
        dingding_login_record_co.insert_one(dingding_login_record_co_new)

    return {"nick": nick, "openid": openid, "code": code}


@app.route('/appId', methods=['GET'])
def appid():
    return app_conf["dingding"]["login"]["appid"]


@app.route('/dingding_scan', methods=['GET'])
def dingding_scan():
    return dingding()


base_dingding_login_url_prefix = "https://oapi.dingtalk.com/connect/oauth2/sns_authorize"


@app.route('/proxy_net_request', methods=['POST'])
def proxy_net_request():
    request_data = request.get_data()
    request_data = json.loads(request_data)
    url = base_dingding_login_url_prefix + request_data["url"]
    method = request_data["method"]
    request_data = {}
    if not request_data.__contains__("request_params"):
        request_params = {}
    else:
        request_params = request_data["request_params"]
    if not request_data.__contains__("request_data"):
        request_data = {}
    else:
        request_data = request_data["request_data"]

    res_result = requests.request(method=method, url=url, params=request_params, data=request_data).json()
    return res_result
