from flask import Blueprint

import config
from common import common_service

app = Blueprint('encrypt_tool', __name__, url_prefix='/encrypt_tool')


@app.route('/encrypt', methods=['POST'])
def encrypt():
    request_data = common_service.check_request_dat_not_null(["encrypt_value"])
    encrypt_value = request_data["encrypt_value"]
    return config.get_encrypt_value(encrypt_value)
