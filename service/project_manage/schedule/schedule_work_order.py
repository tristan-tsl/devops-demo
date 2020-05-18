import json
import os

from bson.json_util import dumps
from bson.objectid import ObjectId
from flask import Blueprint

from common import common_service
from component.my_mongo import mongodb
from component.my_server import MyServer
from config import project_root_path
from service.asset_manage import server_manage
from service.project_manage.schedule import schedule_server_config
from service.project_manage.work_order_process import run_manage

app = Blueprint('project_manage__schedule__schedule_work_order', __name__,
                url_prefix='/project_manage/schedule/schedule_work_order')

project_manage__work_order_process__run_manage_process__schedule_work_order_co = mongodb[
    'project_manage__work_order_process__run_manage_process__schedule_work_order']
project_manage__work_order_process__run_manage_result_log_co = mongodb[
    'project_manage__work_order_process__run_manage_result_log']
project_manage__work_order_process__run_manage_process__schedule_work_order_rb_co = mongodb[
    'project_manage__work_order_process__run_manage_process__schedule_work_order_rb']
project_manage__schedule__schedule_work_order__lock_co = mongodb['project_manage__schedule__schedule_work_order__lock']
project_manage__work_order_process__run_manage_co = mongodb['project_manage__work_order_process__run_manage']

process_v1 = ["dev -> dev_team"]


@app.route('/get_process', methods=['GET'])
def get_process():
    return json.dumps(process_v1)


@app.route('/crontab_file_content_list', methods=['POST'])
def get_crontab_file_content_list():
    try:
        request_data = common_service.check_request_dat_not_null(["env", "host"])
        env = request_data["env"]
        host = request_data["host"]
        host = host.replace(".", "_")
        # 判断来访数据合理性
        schedule_server_config_datas = json.loads(schedule_server_config.get())
        schedule_server_config_data = schedule_server_config_datas[0]
        schedule_server_config_data_data = schedule_server_config_data["schedule_server_config"]
        level_env = schedule_server_config_data_data[env]
        level_host = level_env[host]
        if not level_host:
            raise common_service.MyServiceException("非法入侵, 该服务器不存在调度服务器配置数据中")
        # 获取服务器连接信息
        server_manage_datas = json.loads(server_manage.get_decrypt())
        server_manage_data = server_manage_datas[0]
        server_manage_data_data = server_manage_data["server_manage"]
        server_manage_level_host = server_manage_data_data[host]
        conn_host = host.replace("_", ".")
        for key in server_manage_level_host:
            username = key
            password = server_manage_level_host[username]
            my_server = MyServer(conn_host, username, password)
            filepath = "/etc/crontab"
            file_content = my_server.get_file_content(filepath)
            result = {}
            for index, item in enumerate(file_content):
                result[index] = item
            return result
            break
    except common_service.MyServiceException as e:
        return common_service.ResResult.return500(str(e))


process_type = "schedule_manage"


@app.route('/request_schedule_work_order', methods=['POST'])
def request_schedule_work_order():
    try:
        # 之前配置的
        old_crontab_file_content_list = get_crontab_file_content_list()

        request_data = common_service.check_request_dat_not_null(["env", "host", "process_template_id"])
        title = request_data["title"]
        env = request_data["env"]
        process_template_id = request_data["process_template_id"]
        host_original = request_data["host"]
        modify_schedule_line_req = request_data["modify_schedule_line"]
        apply_process = request_data["apply_process"]
        host = host_original.replace(".", "_")

        # 解析数据
        modify_schedule_line_display = ""
        log = "为回滚做好准备,具体内容为: <br/>"
        is_has_data = False
        old_modify_schedule_line = {}
        modify_schedule_line = {}
        for item in modify_schedule_line_req:
            is_has_data = True
            line_content = modify_schedule_line_req[item]
            old_line_content = old_crontab_file_content_list[int(item)]
            old_modify_schedule_line[str(item)] = old_line_content
            modify_schedule_line_display += "-" * 100
            modify_schedule_line_display += "修改第%s行:\n %s \n==>\n %s\n" % (item, old_line_content, line_content)
            log += "还原第%s行:<br/> %s <br/>==><br/> %s<br/>" % (item, line_content, old_line_content)
            modify_schedule_line[str(item)] = line_content
        if not is_has_data:
            raise common_service.MyServiceException("需要修改的计划任务的内容不能为空")

        # 加锁 一个服务同时只能有一个流程在跑,否则就会造成数据混乱
        is_locked = True
        is_exist_host_lock_data = False
        project_manage__schedule__schedule_work_order__lock_data = json.loads(
            dumps(project_manage__schedule__schedule_work_order__lock_co.find_one(
                filter={'host': host})))
        if project_manage__schedule__schedule_work_order__lock_data:
            is_exist_host_lock_data = True
            process_id = project_manage__schedule__schedule_work_order__lock_data["process_id"]
            project_manage__work_order_process__run_manage_data = project_manage__work_order_process__run_manage_co \
                .find_one(filter={'_id': ObjectId(process_id)})
            if project_manage__work_order_process__run_manage_data and \
                    project_manage__work_order_process__run_manage_data["status"] != "RUNNING":
                is_locked = False
        else:
            is_locked = False
        if is_locked:
            raise common_service.MyServiceException("操作失败,修改服务器的计划任务文件的操作只能同时只有一个流程在跑,否则就会造成数据混乱")

        # 判断时间
        # 流程
        finish_result = {
            "method": "POST",
            "url": "http://localhost:8080/project_manage/schedule/schedule_work_order/finish_process",
            "rb_url": "http://localhost:8080/project_manage/schedule/schedule_work_order/rollback_process",
        }
        display_content = "执行环境为: %s \n 调度服务器为: %s \n 修改调度的内容为: \n %s \n\n\n " % (
            env, host, modify_schedule_line_display)

        process_id, next_step = run_manage.process_start(apply_process, process_type, finish_result, title,
                                                         display_content, env, process_template_id,
                                                         system_tag=host_original)
        # 存储内容等待流程完成时去执行
        project_manage__work_order_process__run_manage_process__schedule_work_order_co.insert_one({
            "process_id": process_id,
            "env": env,
            "host": host,
            "modify_schedule_line": modify_schedule_line
        })
        # 生成备份文件
        project_manage__work_order_process__run_manage_process__schedule_work_order_rb_co.insert_one({
            "process_id": process_id,
            "env": env,
            "host": host,
            "modify_schedule_line": old_modify_schedule_line,
        })
        # 插入日志
        project_manage__work_order_process__run_manage_result_log_co.insert_one({
            "process_id": process_id,
            "log": log,
            "is_exe_success": True,
        })
        # 更新锁的流程
        if is_exist_host_lock_data:
            project_manage__schedule__schedule_work_order__lock_co.update_one(filter={'host': host},
                                                                              update={'$set': {
                                                                                  "process_id": process_id
                                                                              }})
        else:
            project_manage__schedule__schedule_work_order__lock_co.insert_one({"host": host, "process_id": process_id})
        run_manage.process_after_trigger(process_id, next_step)

        return {}
    except common_service.MyServiceException as e:
        return common_service.ResResult.return500(str(e))


def do_process(host, modify_schedule_line, process_instance_id):
    # 形成新的文件内容
    # 查找原始文件内容
    server_manage_datas = json.loads(server_manage.get_decrypt())
    server_manage_data = server_manage_datas[0]
    server_manage_data_data = server_manage_data["server_manage"]
    server_manage_level_host = server_manage_data_data[host]
    conn_host = host.replace("_", ".")
    for key in server_manage_level_host:
        username = key
        password = server_manage_level_host[username]
        my_server = MyServer(conn_host, username, password)
        filepath = "/etc/crontab"
        file_content = my_server.get_file_content(filepath)
        break
    # 修改原始文件内容为新的文件内容
    for key in modify_schedule_line:
        file_content[int(key)] = modify_schedule_line[key]
    project_manage__work_order_process__run_manage_result_log_co.insert_one({
        "process_id": process_instance_id,
        "log": "crontab文件内容为:" + str(file_content) + "<br/>",
        "is_exe_success": True,
    })
    # 将数据保存到本地文件
    local_schedule_path = os.path.join(project_root_path, "temp", "schedule")
    if not os.path.exists(local_schedule_path):
        os.mkdir(local_schedule_path)
    local_schedule_host_path = os.path.join(local_schedule_path, host)
    with open(local_schedule_host_path, "w", encoding="utf-8") as local_file:
        local_file.writelines(file_content)
    project_manage__work_order_process__run_manage_result_log_co.insert_one({
        "process_id": process_instance_id,
        "log": "在本地创建文件",
        "is_exe_success": True,
    })
    # 修改远程服务器的crontab文件内容
    filepath_new_backup = "/etc/crontab_new_backup"
    filepath_old_backup = "/etc/crontab_old_backup"
    filepath = "/etc/crontab"
    my_server = MyServer(conn_host, username, password)
    # # 备份文件
    my_server.backup_file(filepath, filepath_old_backup)
    project_manage__work_order_process__run_manage_result_log_co.insert_one({
        "process_id": process_instance_id,
        "log": "备份远程服务器的crontab文件(%s -> %s)" % (filepath, filepath_old_backup),
        "is_exe_success": True,
    })
    # # 上传文件
    my_server.upload_local_file(local_schedule_host_path, filepath_new_backup)
    project_manage__work_order_process__run_manage_result_log_co.insert_one({
        "process_id": process_instance_id,
        "log": "上传本地文件到远程服务(%s -> %s)" % (local_schedule_host_path, filepath_new_backup),
        "is_exe_success": True,
    })
    # 移动文件
    my_server.backup_file(filepath_new_backup, filepath)
    project_manage__work_order_process__run_manage_result_log_co.insert_one({
        "process_id": process_instance_id,
        "log": "移动覆盖原来的crontab文件(%s -> %s)" % (filepath_new_backup, filepath),
        "is_exe_success": True,
    })
    # 解锁
    project_manage__schedule__schedule_work_order__lock_co.delete_one(
        {"host": host, "process_id": process_instance_id})


@app.route('/finish_process', methods=['POST'])
def finish_process():
    try:
        request_data = common_service.check_request_dat_not_null(["process_instance_id"])
        process_instance_id = request_data["process_instance_id"]
        try:
            # 查询对应流程id的执行内容
            db_res_data = json.loads(
                dumps(project_manage__work_order_process__run_manage_process__schedule_work_order_co.find_one(
                    filter={'process_id': process_instance_id})))
            env = db_res_data["env"]
            host = db_res_data["host"]
            modify_schedule_line = db_res_data["modify_schedule_line"]

            do_process(host, modify_schedule_line, process_instance_id)
            run_manage.upgrade_process_service_invoke_status(process_instance_id, True)
            return {}
        except Exception as e:
            project_manage__work_order_process__run_manage_result_log_co.insert_one({
                "process_id": process_instance_id,
                "log": "异常:" + str(e),
                "is_exe_success": True,
            })
            run_manage.upgrade_process_service_invoke_status(process_instance_id, False)
            raise e
    except common_service.MyServiceException as e:

        print(e)
        return common_service.ResResult.return500(str(e))


@app.route('/rollback_process', methods=['POST'])
def rollback_process():
    try:
        request_data = common_service.check_request_dat_not_null(["process_instance_id"])
        process_instance_id = request_data["process_instance_id"]
        # 查询对应流程id的执行内容
        db_res_data = json.loads(
            dumps(project_manage__work_order_process__run_manage_process__schedule_work_order_rb_co.find_one(
                filter={'process_id': process_instance_id})))
        env = db_res_data["env"]
        host = db_res_data["host"]
        modify_schedule_line = db_res_data["modify_schedule_line"]

        do_process(host, modify_schedule_line, process_instance_id)
        return {}
    except common_service.MyServiceException as e:
        print(e)
        return common_service.ResResult.return500(str(e))
