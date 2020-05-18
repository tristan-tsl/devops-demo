import threading

import requests


def do_check():
    try:
        requests.get("http://localhost:8080/project_manage/associate_db/sql_work_order/check_mysql_dumper")
    except Exception as e:
        print(e)


def check():
    threading.Thread(target=do_check, name='do_check').start()
