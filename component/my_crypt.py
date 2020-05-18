# 加密参考文档: https://cryptography.io/en/latest/
import yaml
from cryptography.fernet import Fernet

import config

ENCODING_STR = "utf8"


def gen_crypt_key():
    return Fernet.generate_key()


def do_encrypt_value(key, target_value):
    return str(Fernet(key).encrypt(bytes(target_value, encoding=ENCODING_STR)), encoding=ENCODING_STR)


def do_decrypt_value(key, encrypt_value):
    return str(Fernet(key).decrypt(bytes(encrypt_value, encoding=ENCODING_STR)), encoding=ENCODING_STR)


def decrypt_enc_part(original_data_str):
    config_file_content = ""
    enc_start_content = ""
    enc_content = ""
    for s in original_data_str:
        if enc_start_content == "" and s == "E":
            enc_start_content += s
        elif enc_start_content == "E" and s == "N":
            enc_start_content += s
        elif enc_start_content == "EN" and s == "C":
            enc_start_content += s
        elif enc_start_content == "ENC" and s == "(":
            enc_start_content += s
        elif enc_start_content == "ENC(" and s != ")":
            enc_content += s
        elif enc_start_content == "ENC(" and s == ")":
            dec_content = do_decrypt_value(config.devops_platform_project_crypto_key, enc_content)
            config_file_content += dec_content
            enc_start_content = ""
            enc_content = ""
        else:
            config_file_content += enc_start_content+s
            enc_start_content = ""
    return yaml.safe_load(config_file_content)
