from flask import Blueprint

from common import common_service
from component.my_mongo import mongodb

app = Blueprint('asset_manage__deploy_server__project_composition',
                                                             __name__,
                                                             url_prefix='/asset_manage/deploy_server'
                                                                        '/project_composition')
asset_manage__deploy_server__project_composition_co = mongodb['asset_manage__deploy_server__project_composition']
if not asset_manage__deploy_server__project_composition_co.find_one():
    asset_manage__deploy_server__project_composition_co.insert_one({"project_composition": {}, })


@app.route('/get', methods=['GET'])
def get():
    return common_service.query(asset_manage__deploy_server__project_composition_co)


@app.route('/put', methods=['PUT'])
def put():
    return common_service.insert(asset_manage__deploy_server__project_composition_co)
