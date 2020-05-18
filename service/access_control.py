import json
import os

import yaml
from bson.json_util import dumps
from bson.objectid import ObjectId
from flask import Blueprint, session

import config
from common import common_service
from component.my_mongo import mongodb

app = Blueprint('access_control', __name__, url_prefix='/access_control')

access_control_auth_term_co = mongodb['access_control_auth_term']  # 权限单元
access_control_group_struct_co = mongodb['access_control_group_struct']  # 组织架构
access_control_user_manage_co = mongodb['access_control_user_manage']  # 用户管理
access_control_user_manage_has_label_co = mongodb['access_control_user_manage_has_label']  # 用户拥有的标签
access_control_label_manage_co = mongodb['access_control_label_manage']  # 标签管理

access_control_group_struct_has_user_co = mongodb['access_control_group_struct_has_user']  # 组织拥有的人

dingding_user_info_co = mongodb['dingding_user_info']
if not access_control_auth_term_co.find_one():
    access_control_auth_term_co.insert_one({"data": {}})
if not access_control_group_struct_co.find_one():
    access_control_group_struct_co.insert_one({"data": {}})
if not access_control_user_manage_co.find_one():
    access_control_user_manage_co.insert_one({"data": {}})


@app.route('/auth_term', methods=['GET'])
def get_access_control_auth_term():
    with open(os.path.join(config.project_root_path, "init_data", "access_control", "auth_term.json"),
              encoding="utf-8") as f:
        file_content = f.read()
        return file_content


@app.route('/group_struct', methods=['GET'])
def get_access_control_group_struct():
    with open(os.path.join(config.project_root_path, "init_data", "access_control", "group_struct.json"),
              encoding="utf-8") as f:
        file_content = f.read()
        return file_content


@app.route('/user_manage', methods=['GET'])
def get_access_control_user_manage():
    return dumps(dingding_user_info_co.find())


@app.route('/label_manage', methods=['GET'])
def get_access_control_label_manage():
    return dumps(access_control_label_manage_co.find())


@app.route('/my_label', methods=['GET'])
def get_access_control_my_label():
    return dumps(["system_manager"])


@app.route('/label_manage', methods=['POST'])
def add_access_control_label_manage():
    try:
        request_data = common_service.check_request_dat_not_null(["name", "code"])
        name = request_data["name"]
        code = request_data["code"]
        access_control_label_manage_co.insert_one({"name": name, "code": code})
        return {}
    except common_service.MyServiceException as e:
        print(e)
        return common_service.ResResult.return500(str(e))


@app.route('/label_manage', methods=['PUT'])
def modify_access_control_label_manage():
    try:
        request_data = common_service.check_request_dat_not_null(["id", "name", "code"])
        data_id = request_data["id"]
        name = request_data["name"]
        code = request_data["code"]
        access_control_label_manage_co.update_one(filter={'_id': ObjectId(data_id)},
                                                  update={'$set': {
                                                      "name": name,
                                                      "code": code
                                                  }})
        return {}
    except common_service.MyServiceException as e:
        print(e)
        return common_service.ResResult.return500(str(e))


@app.route('/label_manage', methods=['DELETE'])
def delete_access_control_label_manage():
    try:
        request_data = common_service.check_request_dat_not_null(["id"])
        data_id = request_data["id"]
        access_control_label_manage_co.delete_one(filter={'_id': ObjectId(data_id)})
        return {}
    except common_service.MyServiceException as e:
        print(e)
        return common_service.ResResult.return500(str(e))


@app.route('/group_struct_has_auth_term', methods=['POST'])
def get_group_struct_has_auth_term():
    try:
        request_data = common_service.check_request_dat_not_null(["group_struct"])
        group_struct = request_data["group_struct"]
        with open(os.path.join(config.project_root_path, "init_data", "access_control", "group_struct_has_auth_term",
                               group_struct + ".json"),
                  encoding="utf-8") as f:
            file_content = f.read()
            return file_content
    except common_service.MyServiceException as e:
        print(e)
        return common_service.ResResult.return500(str(e))


@app.route('/my_group_struct_has_static_page', methods=['GET'])
def get_my_group_struct_has_static_page():
    try:
        res_result = {}
        # 当前登录人所在的组织架构
        my_open_id = session["user_id"]
        my_group_struct_list = json.loads(
            dumps(access_control_group_struct_has_user_co.find({"user_open_id": my_open_id})))
        if not my_group_struct_list or len(my_group_struct_list) < 1:
            return res_result
        for my_group_struct_item in my_group_struct_list:
            my_group_struct = my_group_struct_item["group_struct"]
            file_path = os.path.join(config.project_root_path, "init_data", "access_control",
                                     "group_struct_has_static_page", my_group_struct + ".yml")
            if not os.path.exists(file_path):
                continue
            with open(file_path, encoding="utf-8") as f:
                file_content = f.read()
                if "*" != file_content:
                    data_obj = yaml.safe_load(file_content)
                    res_result = data_obj
                else:
                    res_result = {"*": None}
                    break
        return res_result
    except common_service.MyServiceException as e:
        print(e)
        return common_service.ResResult.return500(str(e))


@app.route('/group_struct_has_user', methods=['POST'])
def get_group_struct_has_user(group_struct=None):
    try:
        if not group_struct:
            request_data = common_service.check_request_dat_not_null(["group_struct"])
            group_struct = request_data["group_struct"]
        access_control_group_struct_has_user_db_res = json.loads(
            dumps(access_control_group_struct_has_user_co.find({"group_struct": group_struct})))

        for item in access_control_group_struct_has_user_db_res:
            user_open_id = item["user_open_id"]
            item["label"] = json.loads(
                dumps(access_control_user_manage_has_label_co.find_one({"user_open_id": user_open_id})))["label"]

        return json.dumps(access_control_group_struct_has_user_db_res)
    except common_service.MyServiceException as e:
        print(e)
        return common_service.ResResult.return500(str(e))


@app.route('/group_struct_has_user', methods=['PUT'])
def modify_group_struct_has_user():
    try:
        request_data = common_service.check_request_dat_not_null(["group_struct", "user", "label", "action"])
        group_struct = request_data["group_struct"]
        user = request_data["user"]
        label = request_data["label"]
        # action = request_data["action"]

        access_control_group_struct_has_user_db_res = access_control_group_struct_has_user_co.find_one({
            "group_struct": group_struct,
            "user_open_id": user,
        })
        if not access_control_group_struct_has_user_db_res:
            # 查询该用户的nick
            user_info_data = json.loads(dumps(dingding_user_info_co.find_one({"openid": user})))
            nick = user_info_data["nick"]
            access_control_group_struct_has_user_co.insert_one({
                "group_struct": group_struct,
                "user_open_id": user,
                "nick": nick
            })
        access_control_user_manage_has_label_db_res = access_control_user_manage_has_label_co.find_one({
            "user_open_id": user
        })
        if not access_control_user_manage_has_label_db_res:
            access_control_user_manage_has_label_co.insert_one({
                "user_open_id": user,
                "label": label
            })
        else:
            access_control_user_manage_has_label_co.update_one(
                filter={"user_open_id": user},
                update={'$set': {
                    "label": label
                }})
        return {}
    except common_service.MyServiceException as e:
        print(e)
        return common_service.ResResult.return500(str(e))


@app.route('/group_struct_has_user', methods=['DELETE'])
def delete_group_struct_has_user():
    try:
        request_data = common_service.check_request_dat_not_null(["group_struct", "user_open_id"])
        group_struct = request_data["group_struct"]
        user_open_id = request_data["user_open_id"]
        # user_id = session["user_id"]
        # if user_id == user_open_id:
        #     raise common_service.MyServiceException("用户不能删除自己的权限")
        access_control_group_struct_has_user_co.delete_one(filter={
            "group_struct": group_struct,
            "user_open_id": user_open_id
        })
        return {}
    except common_service.MyServiceException as e:
        print(e)
        return common_service.ResResult.return500(str(e))
    pass


def get_user_label_list(user_open_id):
    return json.loads(dumps(access_control_user_manage_has_label_co.find_one({"user_open_id": user_open_id})))["label"]
