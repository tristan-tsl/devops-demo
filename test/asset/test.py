import json
import config

moni_test_data_value = {
    "mysql": {
        "dev": {
            "192_168_71_96:3306": {
                "name": "自动化运维管理测试环境",
                "host_port": "192.168.71.96:3306",
                "username": "root",
                "password": "ENC(gAAAAABdjcznyObpsNpWljCpEtgFhnzXQ9E4caj5jGziKYvIWJdcaVkR_G-7WMz9cp-yMhA9UvCvvHDgT6C4tT6dtxBdeWoJjw==)"
            },
            "192_168_71_214:3306": {
                "name": "测试环境ERP库",
                "host_port": "192.168.71.214:3306",
                "username": "autoops",
                "password": "ENC(gAAAAABdjc8XDiaHw-lKaAQlGqxMjzwlKGWM2X7Q_pUApUXrYsRK5kXbNGYE6qyowcCszha2yRDhR8kDIMB4nanqaj6HaPn9Ow==)"
            }
        }
    }
}
MEMORY_CACHE_TAG = "svn"

if __name__ == '__main__':
    print(config.get_decrypt_value(json.dumps(moni_test_data_value)))
    pass
