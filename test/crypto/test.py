import os

from component import my_crypt

DEVOPS_PLATFORM_PROJECT_CRYPTO_KEY_STR = "devops_platform_project_crypto_key"
devops_platform_project_crypto_key = os.environ.get(DEVOPS_PLATFORM_PROJECT_CRYPTO_KEY_STR)

test_target_values = [
    "Ybautoops2019",
]


def test_encrypt():
    for target_value in test_target_values:
        encrypt_value = my_crypt.do_encrypt_value(devops_platform_project_crypto_key, target_value)
        print("target_value: ", target_value, "encrypt_value: ", "ENC(" + encrypt_value + ")")


if __name__ == '__main__':
    test_encrypt()
    pass
    # test_key = "DGYAMW6jVw2ojR-HRx0kMtFt6jYjOgG_AzXLjymK6l4="
    # print("encrypt_value: ", encrypt_value)
    # decrypt_value = my_crypt.do_decrypt_value(test_key, encrypt_value)
    # print("decrypt_value: ", decrypt_value)
