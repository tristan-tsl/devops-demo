"""
元数据管理

数据格式:

parent_asset_type: "上级资产类型"
asset_type: "资产类型"
asset_type_title: "资产类型标题"
env: "环境"

"""
import json

from bson.json_util import dumps
from flask import Blueprint, request

from common import common_service
from common.common_service import MyServiceException, ResResult
from component import my_data_struct2
from component.my_mongo import mongodb

app = Blueprint('general_asset_manage_system__metadata_manage', __name__,
                url_prefix='/general_asset_manage_system/metadata_manage')

general_asset_manage_system__metadata_co = mongodb['general_asset_manage_system__metadata']

"""
初始化数据:
[
{"pid": "", "id": "1", "name": "服务器"}
,{"pid": "", "id": "2", "name": "数据库"}
,{"pid": "2", "id": "2_1", "name": "MySQL"}
,{"pid": "2", "id": "2_2", "name": "Oracle"}
,{"pid": "", "id": "3", "name": "容器调度"}
,{"pid": "3", "id": "3_1", "name": "K8S"}
,{"pid": "", "id": "4", "name": "构建服务"}
,{"pid": "4", "id": "4_1", "name": "Jenkins"}
,{"pid": "", "id": "5", "name": "源码"}
,{"pid": "5", "id": "5_1", "name": "SVN"}
]
"""


@app.route('/insert', methods=['POST'])
def insert():
    """
    插入
    """
    try:
        request_data = common_service.check_request_dat_not_null(["pid", "slice_len"])
        pid = request_data["pid"]
        slice_len = request_data["slice_len"]
        slice_len = str(int(slice_len) + 1)
        print("插入数据: ", "pid=", pid, "slice_len=", slice_len)
        if "root" == pid:
            pid = ""
            _id = str(slice_len)
        else:
            _id = str(pid) + "_" + slice_len
        general_asset_manage_system__metadata_co.insert_one({
            "pid": str(pid), "id": str(_id), "name": "", "env": "dev", "env_name": "开发环境"
        })
        return {"id": _id}
    except MyServiceException as e:
        print(e)
        return ResResult.return500(str(e))


@app.route('/delete', methods=['POST'])
def delete():
    """
    删除
    """
    try:
        request_data = common_service.check_request_dat_not_null(["id"])
        _id = request_data["id"]
        if not _id or _id == "":
            raise MyServiceException("不能删除空id节点")
        # 删除指定id节点
        general_asset_manage_system__metadata_co.delete_one(filter={
            "id": _id
        })
        # 删除子节点
        general_asset_manage_system__metadata_co.delete_many(filter={
            "id": {'$regex': "^" + _id + ".*"}
        })
        return {}
    except MyServiceException as e:
        print(e)
        return ResResult.return500(str(e))


@app.route('/update', methods=['POST'])
def update():
    """
    修改
    """
    try:
        request_data = common_service.check_request_dat_not_null(["id", "name"])
        _id = request_data["id"]
        name = request_data["name"]
        if not _id or _id == "":
            raise MyServiceException("不能修改空id节点")
        process_instance = {
            "name": name
        }
        general_asset_manage_system__metadata_co.update_one(filter={'id': _id},
                                                            update={'$set': process_instance})
    except MyServiceException as e:
        print(e)
        return ResResult.return500(str(e))
    return {}


@app.route('/select', methods=['POST'])
def select():
    """
    查询
    """
    request_data = request.get_data()
    # 搜索
    # 分页
    return dumps(general_asset_manage_system__metadata_co.find())


@app.route('/select_tree', methods=['POST'])
def select_tree():
    """
    查询-树状
    """
    metadata_db_result = json.loads(select())
    print("metadata_db_result:", metadata_db_result)
    tree_data = my_data_struct2.List.convert_to_tree(metadata_db_result)
    res_result = [{
        "id": "root",
        "title": "根目录",
        "spread": True,
        "children": tree_data}]
    return json.dumps(res_result)


def get_asset_type_by_asset_type_str(asset_type_str):
    db_query_res = json.loads(dumps(general_asset_manage_system__metadata_co.find_one(filter={
        "name": asset_type_str
    })))
    if db_query_res:
        return db_query_res["id"]
    return None
