from flask import Blueprint

from common import common_service
from component.my_mongo import mongodb

app = Blueprint('project_manage__schedule__schedule_server_config', __name__,
                url_prefix='/project_manage/schedule/schedule_server_config')
project_manage__schedule__schedule_server_config_co = mongodb['project_manage__schedule__schedule_server_config']
if not project_manage__schedule__schedule_server_config_co.find_one():
    project_manage__schedule__schedule_server_config_co.insert_one({"schedule_server_config": {}, })


@app.route('/get', methods=['GET'])
def get():
    return common_service.query(project_manage__schedule__schedule_server_config_co)


@app.route('/put', methods=['PUT'])
def put():
    return common_service.insert(project_manage__schedule__schedule_server_config_co)
