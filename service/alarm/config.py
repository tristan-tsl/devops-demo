from flask import Blueprint

from common import common_service
from component.my_mongo import mongodb

app = Blueprint('alarm__config', __name__,
                url_prefix='/alarm/config')
# 配置文件
alarm__config_co = mongodb['alarm__config']
if not alarm__config_co.find_one():
    alarm__config_co.insert_one({"alarm__config": {}, })


@app.route('/get', methods=['GET'])
def get():
    return common_service.query(alarm__config_co)


@app.route('/put', methods=['PUT'])
def put():
    return common_service.insert(alarm__config_co)
