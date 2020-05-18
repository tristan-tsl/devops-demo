import os

from flask import Blueprint

from common import common_service
from component.my_mongo import mongodb

app = Blueprint('asset_manage__server_manage', __name__,
                url_prefix='/asset_manage/server_manage')
asset_manage__server_manage_co = mongodb['asset_manage__server_manage']
if not asset_manage__server_manage_co.find_one():
    asset_manage__server_manage_co.insert_one({"server_manage": {}, })

import json
import config


def get_decrypt():
    return config.get_decrypt_value(json.dumps(get()))


@app.route('/get', methods=['GET'])
def get():
    return common_service.query(asset_manage__server_manage_co)


@app.route('/put', methods=['PUT'])
def put():
    return common_service.insert(asset_manage__server_manage_co)


@app.route('/data', methods=['GET'])
def get_data():
    with open(os.path.join(config.project_root_path, "moni_data", "server_manage.json"),
              encoding="utf-8") as f:
        file_content = f.read()
        return file_content
