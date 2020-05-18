import datetime
import threading
import time

from component import my_dingding
from component.my_mongo import mongodb

dingding_co = mongodb['dingding']


def time_refresh_dingding_access_token():
    while True:
        print(datetime.datetime.now().strftime('%Y.%m.%d-%H:%M:%S'), "开始刷新token")
        access_token = my_dingding.get_access_token()
        dingding_co.update_one({}, {
            '$set': {"access_token": access_token,
                     "last_update_date": datetime.datetime.now().strftime('%Y.%m.%d-%H:%M:%S')}})
        print(datetime.datetime.now().strftime('%Y.%m.%d-%H:%M:%S'), "刷新token结束")
        time.sleep(1 * 60 * 60)


def start():
    threading.Thread(target=time_refresh_dingding_access_token, name='get_dingding_access_token').start()
