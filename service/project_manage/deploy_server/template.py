from flask import Blueprint

from common import common_service
from component.my_mongo import mongodb

app = Blueprint('project_manage__deploy_server__template', __name__,
                url_prefix='/project_manage/deploy_server/template')
project_manage__deploy_server__template_co = mongodb['project_manage__deploy_server__template']
if not project_manage__deploy_server__template_co.find_one():
    project_manage__deploy_server__template_co.insert_one({"template": {}, })


@app.route('/get', methods=['GET'])
def get():
    return common_service.query(project_manage__deploy_server__template_co)


@app.route('/put', methods=['PUT'])
def put():
    return common_service.insert(project_manage__deploy_server__template_co)
