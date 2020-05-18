import datetime
import os
from builtins import print

from component.my_server import MyServer
from config import app_conf

mysql__mydumper_server__host = app_conf["mysql"]["mydumper_server"]["host"]
mysql__mydumper_server__username = app_conf["mysql"]["mydumper_server"]["username"]
mysql__mydumper_server__password = app_conf["mysql"]["mydumper_server"]["password"]
mysql__mydumper_server__base_dir_path = "/data/tristan/mysql__mydumper/"

# 模拟数据
# mysql__mydumper_server__host = "192.168.71.96"
# mysql__mydumper_server__username = "root"
# mysql__mydumper_server__password = "yibai#EDC"


def mkdir_tree(dir_tree):
    last_level_dir_path = ""
    for item in dir_tree:
        last_level_dir_path += item
        if not os.path.exists(last_level_dir_path):
            os.mkdir(last_level_dir_path)


def do_loader(host, port, username, password, dir_path):
    execute_result = os.system(
        "myloader -v 3 -h %s -P %s -u %s -p %s -d %s" % (host, port, username, password, dir_path))
    return execute_result


def do_dumper_in_remote(host, port, database, table, username, password, process_id=None):
    log_list = []
    log_list.append("开始导出")
    if not process_id:
        process_id = datetime.datetime.now().strftime('%Y_%m_%d__%H_%M_%S')
    dumper_dir_path = mysql__mydumper_server__base_dir_path + "%s:%s/%s/%s/" % (
        host, port, database, table) + process_id
    # 创建目录 mkdir -p
    my_server = MyServer(mysql__mydumper_server__host, mysql__mydumper_server__username,
                         mysql__mydumper_server__password)
    my_server.create_dir(dumper_dir_path)

    # 生成导出命令
    dumper_command = "mydumper -v 3 -h %s -P %s -u %s -p %s -B %s -T %s --skip-tz-utc --kill-long-queries -o %s" % (
        host, port, username, password, database, table, dumper_dir_path)
    print("dumper_command: ", dumper_command)
    stdin, stdout, stderr = my_server.client.exec_command(dumper_command, bufsize=1)
    stdout_iter = iter(stdout.readline, '')
    stderr_iter = iter(stderr.readline, '')
    for item in stdout_iter:
        log_list.append(item)
    for item in stderr_iter:
        log_list.append(item)
    return dumper_dir_path, log_list


def do_loader_in_remote(host, port, username, password, dumper_dir_path):
    log_list = []
    log_list.append("开始导出")
    my_server = MyServer(mysql__mydumper_server__host, mysql__mydumper_server__username,
                         mysql__mydumper_server__password)
    loader_command = "myloader -v 3 -h %s -P %s -u %s -p %s -d %s" % (host, port, username, password, dumper_dir_path)
    print("loader_command: ", loader_command)
    stdin, stdout, stderr = my_server.client.exec_command(loader_command, bufsize=1)
    stdout_iter = iter(stdout.readline, '')
    stderr_iter = iter(stderr.readline, '')
    for item in stdout_iter:
        log_list.append(item)
    for item in stderr_iter:
        log_list.append(item)
    return log_list


def test_loader(dumper_dir_path):
    host = "192.168.71.96"
    port = "3306"
    username = "root"
    password = "tristan123"
    return do_loader_in_remote(host, port, username, password, dumper_dir_path)


def test_dumper():
    # 模拟数据
    host = "192.168.71.214"
    port = "3306"
    database = "yibai_order"
    table = "yibai_order_other_transaction"
    username = "autoops"
    password = "Ybautoops2019"
    # 执行动作
    return do_dumper_in_remote(host, port, database, table, username, password)


if __name__ == '__main__':
    print("开始测试")
    print("测试导出")
    dumper_dir_path, dumper_log_list = test_dumper()
    for item in dumper_log_list:
        print(item)
    print("导出文件夹为: ", dumper_dir_path)
    print("测试导入")
    loader_log_list = test_loader(dumper_dir_path)
    for item in loader_log_list:
        print(item)
    print("导入完成")
