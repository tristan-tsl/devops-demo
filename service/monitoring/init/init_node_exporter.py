import json

import yaml

from component.my_mongo import mongodb
from component.my_server import MyServer
from service.asset_manage import server_manage
from service.monitoring import config

monitoring__open_monitoring_co = mongodb['monitoring__open_monitoring']

tristan_root_path_str_devops_platform = "/data/tristan/devops_platform"
tristan_root_path_str_prometheus = "/data/tristan/devops_platform/prometheus"
tristan_root_path_str_node_exporter = "/data/tristan/devops_platform/prometheus/node_exporter"
tristan_root_path_str_mysql_exporter = "/data/tristan/devops_platform/prometheus/mysql_exporter"


def add_all_server_to_node_exporter():
    # 获取资产管理中所有的服务器
    server_manage_data = json.loads(server_manage.get_decrypt())[0]
    server_manage_data = server_manage_data["server_manage"]
    server_list = []
    for server_item_key in server_manage_data:
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
        if item + ":9100" not in old_server_ip_list:
            scrape_configs.append({
                "job_name": server_ip,
                "static_configs": [
                    {"targets": [server_ip + ":9100"]}
                ]
            })
            is_update = True

    if not is_update:
        return

    config.put_config_file({"config_file": yaml.safe_dump(prometheus_server_config_content_obj)})


def install_node_exporter(server_ip, server_username, server_password):
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
    monitoring_component_node_exporter = monitoring_component_data["node_exporter"]
    download_url = monitoring_component_node_exporter["download_url"]  # 下载链接
    filename = monitoring_component_node_exporter["filename"]  # 下载链接
    filesize = monitoring_component_node_exporter["filesize"]  # 下载链接
    # version = monitoring_component_node_exporter["version"]  # 版本
    # 推断数据
    download_filename = download_url[download_url.rfind("/") + 1:]

    # 判断是否有根目录
    my_server = MyServer(server_ip, server_username, server_password)
    if not my_server.is_exists_path(tristan_root_path_str_node_exporter):
        # 创建根目录
        my_server.create_dir(tristan_root_path_str_node_exporter)
    # 判断是否存在安装包
    install_package_path = tristan_root_path_str_node_exporter + "/" + download_filename
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
            "wget -P %s -c %s" % (tristan_root_path_str_node_exporter, download_url))
    # 判断安装目录是否存在
    install_unpackage_path = tristan_root_path_str_node_exporter + "/" + filename
    if not my_server.is_exists_path(install_unpackage_path):  # 判断是否有安装目录
        # 解压安装包
        my_server.exe_command(
            "tar -zxvf %s -C %s" % (install_package_path, tristan_root_path_str_node_exporter))
    # 检查进程是否存在
    try:
        my_server.exe_command("ps aux|awk '{print $11}'|grep %s" % (
                install_unpackage_path + "/node_exporter"))
    except:
        # 启动node_exporter\
        exe_result, stdin = my_server.exe_command(install_unpackage_path + "/node_exporter" + " > /dev/null 2>&1 &")
    print("完成检测资产管理中服务器(%s)是否安装并运行最新版本的prometheus:node_exporter监控组件" % server_ip)
    add_all_server_to_node_exporter()


class Init(object):
    @staticmethod
    def do_init(server_ip, server_username, server_password):
        install_node_exporter(server_ip, server_username, server_password)
