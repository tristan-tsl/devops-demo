

from flask import Blueprint

from common import common_service
from component.my_mongo import mongodb

app = Blueprint('asset_manage__code_server__svn', __name__,
                url_prefix='/asset_manage/code_server/svn')
asset_manage__code_server__svn_co = mongodb['asset_manage__code_server__svn']
if not asset_manage__code_server__svn_co.find_one():
    asset_manage__code_server__svn_co.insert_one({"svn": {}, })
import json
import config


def get_decrypt():
    return config.get_decrypt_value(json.dumps(get()))


@app.route('/get', methods=['GET'])
def get():
    data_obj = common_service.query(asset_manage__code_server__svn_co)
    return data_obj


@app.route('/put', methods=['PUT'])
def put():
    return common_service.insert(asset_manage__code_server__svn_co)
