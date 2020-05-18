import json

import pymysql
import yaml
from bson.json_util import dumps

from component.my_mongo import mongodb
from component.my_server import MyServer
from service.asset_manage import server_manage
from service.asset_manage.db_manage import mysql
from service.monitoring import config

monitoring__open_monitoring_co = mongodb['monitoring__open_monitoring']

tristan_root_path_str_devops_platform = "/data/tristan/devops_platform"
tristan_root_path_str_prometheus = "/data/tristan/devops_platform/prometheus"
tristan_root_path_str_node_exporter = "/data/tristan/devops_platform/prometheus/node_exporter"
tristan_root_path_str_mysql_exporter = "/data/tristan/devops_platform/prometheus/mysql_exporter"


def init_mysql_exporter_account(mysql_conn_name, mysql_conn_host, mysql_conn_port, mysql_conn_username,
                                mysql_conn_password):
    # 确定所有的mysql都有exporter账号
    """
    授权语句:
        CREATE USER 'exporter'@'localhost' IDENTIFIED BY 'exporter'
        GRANT PROCESS, REPLICATION CLIENT ON *.* TO 'exporter'@'localhost'
        GRANT SELECT ON performance_schema.* TO 'exporter'@'localhost'
    """
    is_exists_exporter_user = "SELECT EXISTS(SELECT 1 FROM mysql.user WHERE user = 'exporter')"
    create_exporter_user_sql = "CREATE USER 'exporter'@'%s' IDENTIFIED BY 'exporter'" % mysql_conn_host
    is_has_grant_exporter_user_1 = "show grants for exporter@%s" % mysql_conn_host
    grant_exporter_user_sql_1 = "GRANT PROCESS, REPLICATION CLIENT ON *.* TO 'exporter'@'%s'" % mysql_conn_host
    grant_exporter_user_sql_2 = "GRANT SELECT ON performance_schema.* TO 'exporter'@'%s'" % mysql_conn_host
    print("连接到mysql name:%s host:%s port:%s username:%s password:%s" % (
        mysql_conn_name, mysql_conn_host, mysql_conn_host, mysql_conn_username, mysql_conn_password))
    db = pymysql.connect(host=mysql_conn_host, port=int(mysql_conn_port),
                         user=mysql_conn_username, passwd=mysql_conn_password, charset='utf8')
    cursor = db.cursor()
    # 判断是否有该用户
    cursor.execute(is_exists_exporter_user)
    query_result = json.loads(dumps(cursor.fetchall()))
    print("query_result: ", query_result)
    if query_result[0][0] == 0:
        # 创建export用户
        cursor.execute(create_exporter_user_sql)
        query_result = json.loads(dumps(cursor.fetchall()))
        print("query_result: ", query_result)
    # 判断是否有该权限
    cursor.execute(is_has_grant_exporter_user_1)
    query_result = json.loads(dumps(cursor.fetchall()))
    print("query_result: ", query_result)
    is_not_have_grant_1 = True
    is_not_have_grant_2 = True
    for query_result_item in query_result:
        query_result_item_content = query_result_item[0]
        if query_result_item_content.find("PROCESS, REPLICATION CLIENT") > 0:
            is_not_have_grant_1 = False
        if query_result_item_content.find("SELECT") > 0:
            is_not_have_grant_2 = False
    if is_not_have_grant_1:
        cursor.execute(grant_exporter_user_sql_1)
        query_result = json.loads(dumps(cursor.fetchall()))
        print("query_result: ", query_result)
    if is_not_have_grant_2:
        cursor.execute(grant_exporter_user_sql_2)
        query_result = json.loads(dumps(cursor.fetchall()))
        print("query_result: ", query_result)


def init_mysql_install_mysql_exporter(server_ip, server_username, server_password, mysql_conn_host_port):
    """
    安装node_exporter组件
    判断是否有根目录(指定目录是否存在)
        创建根目录: /data/tristan/devops_platform/prometheus/node_exporter
    判断是否需要安装(指定文件是否存在)
        安装node_exporter
            下载node_exporter组件文件到指定/data/tristan/devops_platform/prometheus/node_exporter 目录
            解压文件
            授予执行权限
    判断是否启动(指定进程是否存在)
        启动node_exporter
    :return:
    """
    print("开始检测资产管理中服务器(%s)是否安装并运行最新版本的prometheus:node_exporter监控组件" % server_ip)
    # 获取配置的元数据
    monitoring_component_data_ori = json.loads(config.get())[0]
    monitoring_component_data = monitoring_component_data_ori["monitoring__config"]
    monitoring_component_mysql_exporter = monitoring_component_data["mysql_exporter"]
    download_url = monitoring_component_mysql_exporter["download_url"]  # 下载链接
    filename = monitoring_component_mysql_exporter["filename"]  # 下载链接
    filesize = monitoring_component_mysql_exporter["filesize"]  # 文件大小
    env_name = monitoring_component_mysql_exporter["env_name"]  # 环境变量的名称
    username = monitoring_component_mysql_exporter["username"]  # mysql登录账号
    password = monitoring_component_mysql_exporter["password"]  # mysql登录密码

    # 推断数据
    download_filename = download_url[download_url.rfind("/") + 1:]

    # 判断是否有根目录
    my_server = MyServer(server_ip, server_username, server_password)
    if not my_server.is_exists_path(tristan_root_path_str_mysql_exporter):
        # 创建根目录
        my_server.create_dir(tristan_root_path_str_mysql_exporter)
    # 判断是否存在安装包
    install_package_path = tristan_root_path_str_mysql_exporter + "/" + download_filename
    is_need_download = False
    if not my_server.is_exists_path(install_package_path):
        is_need_download = True
    else:
        # 判断安装包大小是否完整
        exe_result, stdin = my_server.exe_command(
            "du -b %s | awk '{print $1}'" % install_package_path)
        if exe_result != str(filesize) + "\n":
            is_need_download = True
    if is_need_download:
        # 下载node_exporter 安装包
        my_server.exe_command(
            "wget -P %s -c %s" % (tristan_root_path_str_mysql_exporter, download_url))
    # 判断安装目录是否存在
    install_unpackage_path = tristan_root_path_str_mysql_exporter + "/" + filename
    if not my_server.is_exists_path(install_unpackage_path):  # 判断是否有安装目录
        # 解压安装包
        my_server.exe_command(
            "tar -zxvf %s -C %s" % (install_package_path, tristan_root_path_str_mysql_exporter))

    # 检查进程是否存在
    try:
        my_server.exe_command("ps aux|awk '{print $11}'|grep %s" % (
                install_unpackage_path + "/mysqld_exporter"))
    except:
        # 启动 mysql_exporter\
        run_mysql_export_command = 'export "DATA_SOURCE_NAME=exporter:exporter@(%s)/" && ' % mysql_conn_host_port + \
                                   install_unpackage_path + "/mysqld_exporter" + " > /dev/null 2>&1 &"
        my_server.exe_command(run_mysql_export_command)
    print("完成检测资产管理中服务器(%s)是否安装并运行最新版本的prometheus:node_exporter监控组件" % server_ip)


def init_prometheus_server_config_mysql_exporter(server_ip, server_username, server_password, mysql_data_env):
    # 获取资产管理中所有的mysql
    server_list = []
    for server_item_key in mysql_data_env:
        server_item_key = server_item_key.split(":")[0]
        server_ip = server_item_key.replace("_", ".")
        server_list.append(server_ip)
    # 获取当前prometheus server的配置文件内容
    prometheus_config_file_content = json.loads(config.get_config_file())
    config_content = prometheus_config_file_content[0]["config_file"]
    # 加载yml文件为对象
    prometheus_server_config_content_obj = yaml.safe_load(config_content)
    # 添加资产管理中的服务器到prometheus server中
    scrape_configs = prometheus_server_config_content_obj["scrape_configs"]

    old_server_ip_list = []
    for item in scrape_configs:
        static_configs = item["static_configs"]
        static_configs_one = static_configs[0]
        static_configs_targets = static_configs_one["targets"]
        static_configs_targets_one = static_configs_targets[0]
        old_server_ip_list.append(static_configs_targets_one)

    is_update = False
    for item in server_list:
        if item + ":9104" not in old_server_ip_list:
            scrape_configs.append({
                "job_name": "mysql-" + server_ip,
                "static_configs": [
                    {"targets": [server_ip + ":9104"]}
                ]
            })
            is_update = True

    if not is_update:
        return

    config.put_config_file({"config_file": yaml.safe_dump(prometheus_server_config_content_obj)})


def init_mysql_exporter(server_ip, server_username, server_password):
    server_manage_result = json.loads(server_manage.get_decrypt())
    server_manage_data = server_manage_result[0]["server_manage"]
    mysql_result = json.loads(mysql.get_decrypt())[0]
    mysql_data = mysql_result["mysql"]
    mysql_data_env = mysql_data["dev"]
    for item in mysql_data_env:
        mysql_item_data = mysql_data_env[item]
        mysql_conn_name = mysql_item_data["name"]
        mysql_conn_host_port = mysql_item_data["host_port"]
        mysql_conn_host_port_part = mysql_conn_host_port.split(":")
        mysql_conn_host = mysql_conn_host_port_part[0]
        mysql_conn_port = mysql_conn_host_port_part[1]

        mysql_conn_username = mysql_item_data["username"]
        mysql_conn_password = mysql_item_data["password"]
        # 初始化所有的mysql都有exporter账号
        init_mysql_exporter_account(mysql_conn_name, mysql_conn_host, mysql_conn_port, mysql_conn_username,
                                    mysql_conn_password)
        mysql_conn_host_str = mysql_conn_host.replace(".", "_")
        server_manage_item_data = server_manage_data[mysql_conn_host_str]
        server_manage_username = list(server_manage_item_data.keys())[0]
        server_manage_password = server_manage_item_data[server_manage_username]

        # 初始化所有的mysql都安装mysql_exporter
        init_mysql_install_mysql_exporter(mysql_conn_host, server_manage_username, server_manage_password,
                                          mysql_conn_host_port)
    # 确认prometheus server 配置了mysql_exporter
    init_prometheus_server_config_mysql_exporter(server_ip, server_username, server_password, mysql_data_env)


class Init(object):
    @staticmethod
    def do_init(server_ip, server_username, server_password):
        init_mysql_exporter(server_ip, server_username, server_password)
