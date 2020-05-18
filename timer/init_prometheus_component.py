import platform
import threading
import time

import requests

bit_digest, system_name = platform.architecture()
is_windows_system = False
if "WindowsPE" == system_name:
    is_windows_system = True


def init_prometheus_component():
    time.sleep(10)  # 让web环境先加载
    while True:
        if is_windows_system:
            time.sleep(10 * 60)  # 定时检测
        try:
            res_result = requests.post("http://localhost:8080/monitoring/open_monitoring/timer_init")
            if res_result.status_code != 200:
                print("定时初始化promethues组件失败: " + str(res_result.json()))
            else:
                print("定时初始化promethues组件成功: " + str(res_result.json()))
        except Exception as e:
            print(e)
        if not is_windows_system:
            time.sleep(10 * 60)  # 定时检测


def start():
    threading.Thread(target=init_prometheus_component, name='init_prometheus_component').start()
