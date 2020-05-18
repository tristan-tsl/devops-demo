import os

import config
from component import my_crypt

project_root_path = os.getcwd()  # 项目根目录
DEVOPS_PLATFORM_PROJECT_CRYPTO_KEY_STR = "devops_platform_project_crypto_key"
devops_platform_project_crypto_key = os.environ.get(DEVOPS_PLATFORM_PROJECT_CRYPTO_KEY_STR)

app_conf = {}


def init():
    with open(os.path.join(project_root_path, "configs", "application.yml")) as f:
        config.app_conf = my_crypt.decrypt_enc_part(f.read())
    print("app_conf: ", app_conf)


endpoint_list_data = None
access_control__group_struct_has_auth_term = {}
access_control__group_struct_has_static_page = {}


def get_decrypt_value(original_data_str):
    return my_crypt.decrypt_enc_part(original_data_str)


def get_encrypt_value(original_data_str):
    return my_crypt.do_encrypt_value(devops_platform_project_crypto_key, original_data_str)
