import datetime
import json
import os

from bson.json_util import dumps
from flask import Blueprint

from common import common_service
from component.my_mongo import mongodb
from component.my_server import MyServer
from config import project_root_path
from service.alarm import config as alarm_config
from service.asset_manage import server_manage

app = Blueprint('monitoring__config', __name__,
                url_prefix='/monitoring/config')
monitoring__config_co = mongodb['monitoring__config']
if not monitoring__config_co.find_one():
    monitoring__config_co.insert_one({"monitoring__config": {}, })
# 配置文件
monitoring__config_file_co = mongodb['monitoring__config_file']
monitoring__alarm_config_file_co = mongodb['monitoring__alarm_config_file']


@app.route('/get', methods=['GET'])
def get():
    return common_service.query(monitoring__config_co)


@app.route('/put', methods=['PUT'])
def put():
    return common_service.insert(monitoring__config_co)


@app.route('/get_config_file', methods=['GET'])
def get_config_file():
    return common_service.query(monitoring__config_file_co)


@app.route('/get_grafana', methods=['GET'])
def get_grafana():
    level_one_data = json.loads(get())[0]
    level_monitoring__config = level_one_data["monitoring__config"]
    level_monitoring__config_grafana = level_monitoring__config["grafana"]
    return dumps(level_monitoring__config_grafana)


@app.route('/put_config_file', methods=['PUT'])
def put_config_file(request_data=None):
    # 校验入参
    try:
        if not request_data:
            request_data = common_service.check_request_dat_not_null(["config_file"])
        config_file = request_data["config_file"]
        if not config_file or config_file.strip() == "":
            raise common_service.MyServiceException("config_file不能为空")
        # 加载prometheus server服务器
        prometheus_server_config = json.loads(get())[0]["monitoring__config"]["prometheus_server"]
        server = prometheus_server_config["server"]
        config_filepath = prometheus_server_config["config_filepath"]
        load_config_file_command = prometheus_server_config["load_config_file_command"]
        # 推断数据
        config_dir_path = config_filepath[0:config_filepath.rfind("/")]

        # 生成本地文件
        local_monitoring_path = project_root_path + "/" + "temp" + "/" + "monitoring"
        if not os.path.exists(local_monitoring_path):
            os.mkdir(local_monitoring_path)
        local_monitoring_config_file_path = project_root_path + "/" + "temp" + "/" + "monitoring" + "/" + "config_file"
        if not os.path.exists(local_monitoring_config_file_path):
            os.mkdir(local_monitoring_config_file_path)

        cur_file_name = "prometheus-%s.yml" % datetime.datetime.strftime(datetime.datetime.now(), '%Y%m%d_%H%M_%S')
        local_prometheus_yml = local_monitoring_config_file_path + "/" + cur_file_name
        local_file = open(local_prometheus_yml, "w", encoding="utf-8")
        local_file.write(config_file)
        local_file.flush()
        local_file.close()
        # 修改远程服务器的文件内容
        filepath_new_backup = config_dir_path + "/" + cur_file_name
        filepath_old_backup = config_dir_path + "/" + "prometheus-old-backup.yml"
        filepath = config_filepath

        # 获取服务器连接信息
        server_conn_info = json.loads(server_manage.get_decrypt())[0]["server_manage"][server]
        server_ip = server.replace("_", ".")
        server_username = list(server_conn_info.keys())[0]
        server_password = server_conn_info[server_username]

        my_server = MyServer(server_ip, server_username, server_password)
        # # 备份文件
        my_server.backup_file(filepath, filepath_old_backup)
        # # 上传文件
        my_server.upload_local_file(local_prometheus_yml, filepath_new_backup)
        # # 移动文件
        my_server.move_file(filepath_new_backup, filepath)
        # 运行加载配置文件的指令
        my_server.exe_command(load_config_file_command)

        request_data = common_service.clear_id(request_data)
        monitoring__config_file_co.insert(request_data)
        return {}
    except common_service.MyServiceException as e:
        print(e)
        return common_service.ResResult.return500(str(e))


@app.route('/get_alarm_config_file', methods=['POST'])
def get_alarm_config_file():
    request_data = common_service.check_request_dat_not_null(["name"])
    name = request_data["name"]
    if not name or name.strip() == "":
        raise common_service.MyServiceException("name不能为空")
    return dumps(monitoring__alarm_config_file_co.find(filter={"name": name}, limit=1, sort=[("_id", -1)]))


def mkdir_multi_level_dir(base_dir_path, multi_level_dir):
    if not os.path.exists(base_dir_path):
        os.mkdir(base_dir_path)
    old_level_dir = base_dir_path
    for level_dir in multi_level_dir:
        cur_level_dir = old_level_dir + "/" + level_dir
        if not os.path.exists(cur_level_dir):
            os.mkdir(cur_level_dir)


def modify_server_file(service_type, local_dirs, local_file_path, target_file_path, server_ip_tag, file_content,
                       load_config_file_command):
    local_temp_service_dir_path = project_root_path + "/" + "temp" + "/" + service_type
    # 生成本地文件
    mkdir_multi_level_dir(local_temp_service_dir_path, local_dirs)  # 生成基础文件夹
    local_file_path = local_temp_service_dir_path + "/" + local_file_path
    local_file = open(local_file_path, "w", encoding="utf-8")
    local_file.write(file_content)
    local_file.flush()
    local_file.close()

    # 明确文件路径
    filepath_new_backup = target_file_path + "-new"
    filepath_old_backup = target_file_path + "-old"
    filepath = target_file_path

    # 获取服务器连接信息
    server_conn_info = json.loads(server_manage.get_decrypt())[0]["server_manage"][server_ip_tag]
    server_ip = server_ip_tag.replace("_", ".")
    server_username = list(server_conn_info.keys())[0]
    server_password = server_conn_info[server_username]
    my_server = MyServer(server_ip, server_username, server_password)

    # 判断远程文件是否存在
    if not my_server.is_exists_path(filepath):
        my_server.exe_command("echo ''>%s" % filepath)
    # 备份远程服务器文件
    my_server.backup_file(filepath, filepath_old_backup)
    # 上传文件
    my_server.upload_local_file(local_file_path, filepath_new_backup)
    # 覆盖原文件
    my_server.move_file(filepath_new_backup, filepath)
    # 加载配置文件
    my_server.exe_command(load_config_file_command)


@app.route('/put_alarm_config_file', methods=['PUT'])
def put_alarm_config_file():
    try:
        # 入参
        request_data = common_service.check_request_dat_not_null(["config_file", "name"])
        file_content = request_data["config_file"]
        if not file_content or file_content.strip() == "":
            raise common_service.MyServiceException("文件内容不能为空")
        name = request_data["name"]
        # 查询alarm文件位置
        alarm_config_data = json.loads(alarm_config.get())
        alarm_config_data_obj = alarm_config_data[0]
        level_data_alarm__config = alarm_config_data_obj["alarm__config"]
        level_data_component = level_data_alarm__config["component"]
        level_data_name = level_data_component[name]
        config_path = level_data_name["config_path"]  # 文件位置
        # 得到prometheus server 服务器的连接信息
        prometheus_server_config = json.loads(get())[0]["monitoring__config"]["prometheus_server"]
        server_ip_tag = prometheus_server_config["server"]
        config_dirpath = prometheus_server_config["config_dirpath"]
        load_config_file_command = prometheus_server_config["load_config_file_command"]
        # 修改prometheus server 服务器中的文件
        local_dirs = ["rule_files"]
        local_file_path = config_path
        target_file_path = config_dirpath + "/" + config_path
        service_type = "monitoring"
        modify_server_file(service_type, local_dirs, local_file_path, target_file_path, server_ip_tag, file_content,
                           load_config_file_command)
        # 更新数据库数据
        monitoring__alarm_config_file_co.insert(request_data)
        return {}
    except common_service.MyServiceException as e:
        print(e)
        return common_service.ResResult.return500(str(e))
