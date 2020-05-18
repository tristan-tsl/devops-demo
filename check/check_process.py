import threading

import requests


def do_check():
    try:
        requests.get("http://localhost:8080/project_manage/work_order_process/run_manage/check_process_delay_invoke")
    except Exception as e:
        print(e)


def check():
    threading.Thread(target=do_check, name='do_check').start()
