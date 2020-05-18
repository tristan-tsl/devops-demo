import json

from bson.json_util import dumps
from flask import request, make_response


def clear_id(data):
    if not data:
        return data

    def clear_dict_id(dict_data):
        try:
            del dict_data["_id"]
            print(dict_data)
        except:
            pass

    if type(data) == dict:
        clear_dict_id(data)
    elif type(data) == list:
        for item in data:
            clear_dict_id(item)
    return data


def query_all(collection_obj, my_filter={}):
    return dumps(collection_obj.find(filter=my_filter, sort=[("_id", -1)]))


def query(collection_obj):
    return dumps(collection_obj.find(limit=1, sort=[("_id", -1)]))


def insert_object(collection_obj, data_object):
    collection_obj.insert(data_object)


def insert(collection_obj):
    request_data = request.get_data()
    request_data = json.loads(request_data)
    request_data = clear_id(request_data)
    collection_obj.insert(request_data)
    return "SUCCESS"


def check_request_dat_not_null(request_data_key_list):
    request_data = request.get_data()
    return data_contain_key_list(request_data, request_data_key_list)


def data_contain_key_list(request_data, request_data_key_list):
    if not request_data or request_data == "":
        raise MyServiceException("请求参数不能为空")
    request_data = json.loads(request_data)
    if request_data_key_list and type(request_data_key_list) == list:
        for item in request_data_key_list:
            if not request_data.__contains__(item):
                raise MyServiceException("缺少" + item + "参数")
    return request_data


class ResResult(object):
    @staticmethod
    def return500(msg):
        custom_res = make_response(msg)
        custom_res.status = "500"
        return custom_res


class MyServiceException(Exception):
    def __init__(self, msg):
        self.msg = msg


def is_list_has_common(list1, list2):
    if not list1 and not list2:
        return False
    for item1 in list1:
        for item2 in list2:
            if item1 == item2:
                return True
    return False
