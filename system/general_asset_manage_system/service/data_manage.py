"""
数据管理

数据格式:

asset_type: "资产类型"
自定义列
"""
import json

from bson.json_util import dumps
from flask import Blueprint

from common import common_service
from common.common_service import MyServiceException, ResResult
from component.my_mongo import mongodb
from system.general_asset_manage_system.service import metadata_manage

app = Blueprint('general_asset_manage_system__data_manage', __name__,
                url_prefix='/general_asset_manage_system/data_manage')

general_asset_manage_system__data_struct_co = mongodb['general_asset_manage_system__data_struct']
general_asset_manage_system__data_co = mongodb['general_asset_manage_system__data']
"""
初始化数据:

[
{"asset_type":"1","code":"ip","meaning":"服务器ip"},
{"asset_type":"1","code":"port","meaning":"服务器端口"},
{"asset_type":"1","code":"username","meaning":"用户名"},
{"asset_type":"1","code":"password","meaning":"密码"},


]


"""


@app.route('/select_data_struct', methods=['POST'])
def select_data_struct():
    """
    查询数据结构
    """
    try:
        # 搜索
        # 分页
        request_data = common_service.check_request_dat_not_null(["asset_type"])
        asset_type = request_data["asset_type"]
        return dumps(general_asset_manage_system__data_struct_co.find(filter={
            "asset_type": asset_type
        }))
    except MyServiceException as e:
        print(e)
        return ResResult.return500(str(e))


@app.route('/opt_data_struct', methods=['POST'])
def opt_data_struct():
    """
    操作数据结构
    """
    try:
        request_data = common_service.check_request_dat_not_null(["opt_name", "code", "meaning", "asset_type"])
        asset_type = request_data["asset_type"]
        opt_name = request_data["opt_name"]
        code = request_data["code"]
        meaning = request_data["meaning"]
        old_data_struct = json.loads(dumps(general_asset_manage_system__data_struct_co.find(filter={
            "asset_type": asset_type,
            "code": code,
        })))
        if "insert" == opt_name:
            # 校验key唯一性
            if old_data_struct:
                raise MyServiceException("添加失败, 该代码值已经存在,不能重复添加")
            general_asset_manage_system__data_struct_co.insert_one({
                "asset_type": asset_type,
                "code": code,
                "meaning": meaning,
            })
        elif "delete" == opt_name:
            if not old_data_struct:
                raise MyServiceException("删除失败, 该代码值不存在,不能删除空的代码值")
            general_asset_manage_system__data_struct_co.delete_one(filter={
                "asset_type": asset_type,
                "code": code,
            })
        elif "update" == opt_name:
            # 校验key存在性
            if not old_data_struct:
                raise MyServiceException("修改失败, 该代码值不存在,不能修改空的代码值的含义")
            general_asset_manage_system__data_struct_co.update_one(filter={"asset_type": asset_type,
                                                                           "code": code},
                                                                   update={'$set': {
                                                                       "meaning": meaning
                                                                   }})
        return {}
    except MyServiceException as e:
        print(e)
        return ResResult.return500(str(e))


# @app.route('/select_data', methods=['POST'])
# def select_data():
#     """
#     查询数据
#     """
#     try:
#         # 搜索
#         # 分页
#         request_data = common_service.check_request_dat_not_null(["asset_type"])
#         asset_type = request_data["asset_type"]
#         return dumps(general_asset_manage_system__data_co.find(filter={
#             "asset_type": asset_type
#         }))
#     except MyServiceException as e:
#         print(e)
#         return ResResult.return500(str(e))


@app.route('/opt_data', methods=['POST'])
def opt_data():
    """
    操作数据
    """
    try:
        request_data = common_service.check_request_dat_not_null(["opt_name", "asset_type"])
        asset_type = request_data["asset_type"]
        opt_name = request_data["opt_name"]
        del request_data["opt_name"]
        if "insert" == opt_name:
            # 存在性检测
            old_data = json.loads(dumps(general_asset_manage_system__data_struct_co.find(filter=request_data)))
            # 校验key唯一性
            if old_data:
                raise MyServiceException("添加失败, 数据已经存在,不能重复添加")
            general_asset_manage_system__data_co.insert_one(request_data)
        elif "delete" == opt_name:
            del request_data["_id"]
            query_old_data = json.loads(dumps(general_asset_manage_system__data_co.find_one(filter=request_data)))
            if not query_old_data:
                raise MyServiceException("删除失败, 该数据不存在,不能存在的数据")
            general_asset_manage_system__data_co.delete_one(filter=request_data)
        elif "update" == opt_name:
            request_data = common_service.check_request_dat_not_null(["old_data", "new_data"])
            old_data = request_data["old_data"]
            new_data = request_data["new_data"]
            del old_data["_id"]
            del new_data["_id"]
            # 校验key存在性
            query_old_data = json.loads(dumps(general_asset_manage_system__data_co.find_one(filter=old_data)))
            if not query_old_data:
                raise MyServiceException("修改失败, 数据不存在,不能修改空的数据")
            general_asset_manage_system__data_co.update_one(filter=old_data,
                                                            update={'$set': new_data})
        return {}
    except MyServiceException as e:
        print(e)
        return ResResult.return500(str(e))


@app.route('/select_data', methods=['POST'])
def select_data():
    """
    查询数据 分页,搜索
    """
    try:
        page_size = 9999999
        page_no = 1
        # 处理资产类型
        request_data = common_service.check_request_dat_not_null([])
        if request_data.__contains__("asset_type"):
            asset_type = request_data["asset_type"]
        elif request_data.__contains__("asset_type_str"):
            asset_type_str = request_data["asset_type_str"]
            asset_type = metadata_manage.get_asset_type_by_asset_type_str(asset_type_str)
            if not asset_type:
                raise MyServiceException("查询数据没有指定资产类型")

        search = request_data["search"]
        search["asset_type"] = asset_type
        my_filter = search
        # 分页
        page = request_data["page"]
        if page["current"]:
            page_no = page["current"]
        if page["page_size"]:
            page_size = page["page_size"]
        skip = page_size * (page_no - 1)
        return dumps({
            "data": general_asset_manage_system__data_co.find(filter=my_filter, sort=[("_id", -1)]).limit(
                page_size).skip(skip),
            "total": general_asset_manage_system__data_co.find(filter=my_filter, sort=[("_id", -1)]).limit(
                page_size).skip(skip).count(),
        })
    except MyServiceException as e:
        print(e)
        return ResResult.return500(str(e))
