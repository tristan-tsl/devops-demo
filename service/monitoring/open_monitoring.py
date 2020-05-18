import json

from flask import Blueprint, request

from component.my_dingding import MyDDRobot
from component.my_mongo import mongodb
from service.alarm import config as alarm_config
from service.asset_manage import server_manage
from service.monitoring.init import init_mysql_exporter
from service.monitoring.init import init_node_exporter
from service.monitoring.init import init_oracle_exporter
from service.monitoring.init import prepare_init

app = Blueprint('monitoring__open_monitoring', __name__,
                url_prefix='/monitoring/open_monitoring')
monitoring__open_monitoring_co = mongodb['monitoring__open_monitoring']


def do_init_prometheus_component(server_ip, server_username, server_password):
    # prepare
    prepare_init.Init.do_init(server_ip, server_username, server_password)
    # node_exporter
    init_node_exporter.Init.do_init(server_ip, server_username, server_password)
    # mysql_exporter
    init_mysql_exporter.Init.do_init(server_ip, server_username, server_password)
    # oracle_exporter
    init_oracle_exporter.Init.do_init(server_ip, server_username, server_password)


@app.route('/timer_init', methods=['POST'])
def timer_init():
    print("开始检测资产管理中服务器是否安装最新版本的prometheus监控组件")
    server_manage_orin = json.loads(server_manage.get_decrypt())
    if not server_manage_orin:
        return
    server_manage_orin = server_manage_orin[0]
    server_manage_data = server_manage_orin["server_manage"]

    for item_key in server_manage_data:
        server_ip = item_key.replace("_", ".")
        print("开始: 检测: 服务器(%s)" % server_ip)
        server_conn_info = server_manage_data[item_key]
        for server_username in server_conn_info:
            server_password = server_conn_info[server_username]
            do_init_prometheus_component(server_ip, server_username, server_password)
            break

    print("完成检测资产管理中服务器是否安装最新版本的prometheus监控组件")
    return {}


alertmanager_status_meaning = {
    "resolved": "已解决",
    "firing": "出现问题",
}


@app.route('/webhook', methods=['POST'])
def webhook():
    request_form = request.form
    if request_form:
        get_params = json.loads(request_form)
        print(get_params)
    request_data = request.get_data()
    if request_data:
        post_params = json.loads(request_data)
        status_str = alertmanager_status_meaning[post_params["status"]]
        common_annotations = post_params["commonAnnotations"]
        msg = ""
        if common_annotations:
            msg = common_annotations["description"]
        # 获取dingding robot 配置信息
        alarm_config_data = json.loads(alarm_config.get())
        alarm_config_data_obj = alarm_config_data[0]
        alarm__config_dingding_webhook = alarm_config_data_obj["alarm__config"]
        dingding_robots = alarm__config_dingding_webhook["dingding_robots"]
        # 取出一个robot
        for dingding_robot in dingding_robots:
            try:
                my_dd_robot = MyDDRobot(dingding_robot)
                my_dd_robot.send_msg("当前状态: %s\n 提示信息: %s" % (status_str, msg))
                break
            except Exception as e:
                print(e)
    return {}
