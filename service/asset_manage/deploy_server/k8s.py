from flask import Blueprint

from common import common_service
from component.my_mongo import mongodb

app = Blueprint('asset_manage__deploy_server__k8s', __name__,
                url_prefix='/asset_manage/deploy/k8s')
asset_manage__deploy_server__k8s_co = mongodb['asset_manage__deploy_server__k8s']
if not asset_manage__deploy_server__k8s_co.find_one():
    asset_manage__deploy_server__k8s_co.insert_one({"k8s": {}, })

import json
import config


def get_decrypt():
    return config.get_decrypt_value(json.dumps(get()))
@app.route('/get', methods=['GET'])
def get():
    return common_service.query(asset_manage__deploy_server__k8s_co)


@app.route('/put', methods=['PUT'])
def put():
    return common_service.insert(asset_manage__deploy_server__k8s_co)
