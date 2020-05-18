import datetime
import json
import os

import yaml
from bson.json_util import dumps
from flask import request, make_response, session

import config
from component.my_mongo import mongodb

"""
对url进行鉴权
对请求参数进行鉴权

对直接拥有该权限单元的用户放行
对拥有该权限的权限组的用户放行
"""
dingding_login_record_co = mongodb['dingding_login_record']
login_user_operate_log_co = mongodb['login_user_operate_log']  # 登录用户操作日志
access_control_group_struct_has_user_co = mongodb['access_control_group_struct_has_user']

allow_not_auth_access_url = ["/access_control/my_group_struct_has_static_page:get"]


def do_auth():
    cur_request_auth_term = request.path + ":" + request.method.lower()
    # 放行部分接口
    if cur_request_auth_term in allow_not_auth_access_url:
        return
    user_id = session["user_id"]
    # 当前登录人的组织架构id
    my_group_struct_list = json.loads(
        dumps(access_control_group_struct_has_user_co.find({"user_open_id": user_id})))
    if not my_group_struct_list or len(my_group_struct_list) < 1:
        raise CustomAuthException("鉴权失败,用户未存在于任何组织架构中")
    my_group_struct_str_list = []
    for my_group_struct_item in my_group_struct_list:
        my_group_struct_str = my_group_struct_item["group_struct"]
        if "system_manager" == my_group_struct_str:  # 系统管理员不需要鉴权
            return
        my_group_struct_str_list.append(my_group_struct_str)

    do_auth_api(cur_request_auth_term, my_group_struct_str_list)


def convert_auth_term_tree_2_list(group_struct_has_auth_term_obj):
    cur_level_result = []
    for item in group_struct_has_auth_term_obj:
        value = item["value"]
        if item.__contains__("children"):
            children = item["children"]
            converted_data_list = convert_auth_term_tree_2_list(children)
            for converted_data_list_item in converted_data_list:
                cur_level_result.append("/" + value + converted_data_list_item)
        else:
            cur_level_result.append("/" + value)
    return cur_level_result


def do_auth_api(cur_request_auth_term, my_group_struct_str_list):
    for my_group_struct_str_item in my_group_struct_str_list:
        if config.access_control__group_struct_has_auth_term.__contains__(my_group_struct_str_item):
            group_struct_detail_auth_term_list = config.access_control__group_struct_has_auth_term[
                my_group_struct_str_item]
        else:
            file_path = os.path.join(config.project_root_path, "init_data", "access_control",
                                     "group_struct_has_auth_term", my_group_struct_str_item + ".json")
            if not os.path.exists(file_path):
                raise CustomAuthException("鉴权失败,该用户所在组织架构不存在")
            with open(file_path, encoding="utf-8") as f:
                group_struct_has_auth_term_obj = yaml.safe_load(f)
            # 解析精简数据为可用数据
            group_struct_detail_auth_term_list = convert_auth_term_tree_2_list(group_struct_has_auth_term_obj)
            config.access_control__group_struct_has_auth_term[
                my_group_struct_str_item] = group_struct_detail_auth_term_list
        if cur_request_auth_term not in group_struct_detail_auth_term_list:
            raise CustomAuthException("鉴权失败,没有该接口的访问权限")


class CustomAuthException(Exception):
    def __init__(self, msg):
        self.msg = msg


def wrap_authentication():
    """适配鉴权"""
    user_id = None
    request_resource = None
    user_auth = None
    resource_auth_term = None
    resource_auth_group = None

    # 放行
    if "/index.html" == request.path:
        return
    request_resource = {
        "path": request.path,
        "method": request.method
    }
    if "OPTIONS" == request.method:
        return
    # 放行静态资源
    request_resource_path = request_resource["path"]
    if request.base_url.startswith("http://localhost"):  # 本地访问直接放行
        return
    if 1 == 2 \
            or request_resource_path == "/" \
            or request_resource_path.startswith("/js") \
            or request_resource_path.startswith("/css") \
            or request_resource_path.endswith(".html") \
            or request_resource_path.endswith(".jpg") \
            or request_resource_path.endswith(".png") \
            or request_resource_path.endswith(".ico") \
            or request_resource_path.startswith("/login") \
            or request_resource_path.startswith("/monitoring/open_monitoring/webhook") \
            :
        return
    # 用户登录校验
    dingding_login_code = None
    if "token" in request.headers:
        dingding_login_code = request.headers["token"]
        # print("dingding_login_code: ", dingding_login_code)
    if not dingding_login_code:
        raise CustomAuthException("用户未登录:请求未携带用户钉钉code")
    # print("dingding_login_code: ", dingding_login_code)

    dingding_login_record_co_old = dingding_login_record_co.find_one(filter={"code": dingding_login_code})
    if not dingding_login_record_co_old:
        raise CustomAuthException("未授权: 历史登录已失效,请前往首页->工作台->重新登录")

    user_id = dingding_login_record_co_old["openid"]
    if not user_id:
        raise CustomAuthException("当前登录人的openid不能为空")
    session["user_id"] = user_id
    # 登录用户记录操作日志
    login_user_operate_log_co.insert_one({"user_id": user_id,
                                          "user_nick": user_id,
                                          "create_datetime": datetime.datetime.utcnow(),
                                          "access_resource": {
                                              "method": str(request.method),
                                              "path": str(request.path),
                                              "data": str(request.get_data()),
                                              "form": str(request.form),
                                              "headers": str(request.headers),
                                          },
                                          "remote_ip": str(request.remote_addr),
                                          "referrer": str(request.referrer),
                                          })
    # 鉴权
    do_auth()


def get_user_has_auth(user_id, user_auth):
    user_auth_has = []
    if not user_auth or type(user_auth) != dict:
        return user_auth_has
    for key in user_auth:
        user_auth_item = user_auth[key]
        if not user_auth_item:
            continue
        if key == user_id:  # 直接声明
            user_auth_has.extend(user_auth_item["auth"])
        else:  # 寄托声明
            user_auth_value = user_auth[key]
            if user_auth_value.__contains__("has") and user_auth_value.__contains__("auth"):
                has_user = user_auth_value["has"]
                group_auth = user_auth_value["auth"]
                if user_id in has_user:
                    user_auth_has.extend(group_auth)
    return list(set(user_auth_has))


def authentication(user_id, request_resource, user_auth, resource_auth_term, resource_auth_group):
    """
    鉴权
    :param user_id: 用户id
    :param request_resource: 请求的资源
    :param resource_auth_group: 资源授权组
    :param resource_auth_term:  资源授权单元
    :param user_auth: 用户拥有的权限
    :return:
    """
    # 得到用户拥有的权限
    user_auth_has = get_user_has_auth(user_id, user_auth)
    # 转换引用权限为直接权限
    for user_auth_has_key in user_auth_has:
        if user_auth_has_key.startswith("@"):  # 引用权限单元
            resource_auth_group_item = resource_auth_group[user_auth_has_key[1:len(user_auth_has_key)]]
            user_auth_has.extend(resource_auth_group_item)
            user_auth_has.remove(user_auth_has_key)
            pass
    user_auth_has = list(set(user_auth_has))

    # 判断是否拥有权限
    # 该路径直接存在于记录中
    if request_resource["path"] + ":" + request_resource["method"].lower() in user_auth_has:
        # 直接授权
        return
    for user_auth_has_key in user_auth_has:
        if user_auth_has_key.endswith("/*"):
            suffix = user_auth_has_key[0:len(user_auth_has_key) - 1]
            if request_resource["path"].startswith(suffix):
                # *型授权
                return
    raise CustomAuthException("鉴权失败,该用户没有授权")


class RouterPrivilegeAuth:
    def __init__(self):
        pass

    def __call__(self, fn):
        def wrapped(*args, **kwargs):
            try:
                wrap_authentication()
            except CustomAuthException as e:
                print("鉴权失败, 来访用户的ip为: " + request.remote_addr)

                custom_res = make_response(e.msg)
                custom_res.status = "401"
                return custom_res
                return fn()

        return wrapped
