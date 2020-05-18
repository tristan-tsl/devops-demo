import json
import threading

import pymysql
from bson.json_util import dumps
from flask import Blueprint, request

from common import common_service
from common.common_service import ResResult, MyServiceException
from component import my_inception
from component import my_mysql
from component.my_mongo import mongodb
from component.mysql import mydumper_loader
from service.asset_manage.db_manage import mysql
from service.project_manage.work_order_process import run_manage

app = Blueprint('project_manage__associate_db_sql_work_order', __name__,
                url_prefix='/project_manage/associate_db/sql_work_order')
project_manage__associate_db_sql_work_order_co = mongodb['project_manage__associate_db_sql_work_order']
if not project_manage__associate_db_sql_work_order_co.find_one():
    project_manage__associate_db_sql_work_order_co.insert_one({"sql_work_order": {}, })
project_manage__work_order_process__run_manage_process_sql_content_co = mongodb[
    'project_manage__work_order_process__run_manage_process_sql_content']
project_manage__work_order_process__run_manage_result_log_co = mongodb[
    'project_manage__work_order_process__run_manage_result_log']
project_manage__work_order_process__run_manage_process_sql_content_rb_co = mongodb[
    'project_manage__work_order_process__run_manage_process_sql_content_rb']
project_manage__work_order_process__run_manage_process_mysql_dumper_co = mongodb[
    'project_manage__work_order_process__run_manage_process_mysql_dumper']


@app.route('/get_mysql_metadata', methods=['GET'])
def get():
    query_result = json.loads(mysql.get_decrypt())
    if not query_result:
        return {}
    query_result = query_result[0]
    level_mysql = query_result["mysql"]
    if not level_mysql:
        return {}
    for level_env_key, level_env_value in level_mysql.items():
        if not level_env_value:
            continue
        for level_ip_key, level_ip_value in level_env_value.items():
            if not level_ip_value:
                continue
            del level_ip_value["username"]
            del level_ip_value["password"]

    return json.dumps(query_result)


forbid_list = ["information_schema", "mysql", "performance_schema", "sys"]


@app.route('/get_database_by_mysql_instance', methods=['POST'])
def get_database_by_mysql_instance():
    request_data = request.get_data()
    request_data = json.loads(request_data)
    env = request_data["env"]  # "192.168.71.96:3306"
    mysql_host_port = request_data["host_port"]
    if not env or not mysql_host_port:
        return {}
    # 查询对应mysql的元数据
    query_result = json.loads(mysql.get_decrypt())
    if not query_result:
        return {}
    query_result = query_result[0]
    level_mysql = query_result["mysql"]
    if not level_mysql:
        return {}

    level_env = level_mysql[env]
    level_mysql_instance = level_env[mysql_host_port]
    mysql_host_port_or = mysql_host_port.replace("_", ".")
    host = mysql_host_port_or.split(":")[0]
    port = mysql_host_port_or.split(":")[1]
    username = level_mysql_instance["username"]
    password = level_mysql_instance["password"]

    # 连接对应mysql去获取数据库列表信息
    db = pymysql.connect(host=host, port=int(port),
                         user=username, passwd=password, charset='utf8')
    cursor = db.cursor()
    cursor.execute("show databases")
    query_result = dumps(cursor.fetchall())
    query_result_json = json.loads(query_result)
    result = []

    for item in query_result_json:
        for item_item in item:
            # 过滤MySQL自带的数据库
            if item_item not in forbid_list:
                result.append(item_item)

    return dumps(result)


process_type = "sql_invoke"

forbid_sql_type_list = ["DROP"]
DANGER_SQL_STR = "danger_sql"
DB_AUTH_STR = "db_auth"
SQL_INVOKE_STR = "invoke"


@app.route('/do_sql_invoke', methods=['POST'])
def do_sql_invoke():
    try:
        request_data = common_service.check_request_dat_not_null(
            ["title", "env", "host_port", "database", "sql_content", "apply_process", "process_template_id",
             "action_type"])
        title = request_data["title"]
        env = request_data["env"]
        host_port = request_data["host_port"]
        database = request_data["database"]
        sql_content = request_data["sql_content"]
        apply_process = request_data["apply_process"]
        process_template_id = request_data["process_template_id"]
        action_type = request_data["action_type"]
        if "TRUNCATE" in sql_content:
            raise MyServiceException("禁止执行TRUNCATE语法")
        if action_type != DANGER_SQL_STR:
            # 检测是否为危险SQL
            sql_content_list = split_sql_content(sql_content)
            for sql_content_item in sql_content_list:
                for forbid_sql_type_item in forbid_sql_type_list:
                    if sql_content_item.upper().startswith(forbid_sql_type_item):
                        raise MyServiceException("不支持的SQL类型: %s" % forbid_sql_type_item)
        # 检测SQL是否能够执行
        check_sql_executable(env, host_port, database, sql_content)
        # 流程
        finish_result = {
            "method": "POST",
            "url": "http://localhost:8080/project_manage/associate_db/sql_work_order/finish_sql_invoke",
            "rb_url": "http://localhost:8080/project_manage/associate_db/sql_work_order/rollback_sql_invoke",
        }
        display_content = "执行环境为: %s \n MySQL实例为: %s \n 数据库为: %s \n 动作类型为: %s \n  SQL内容为: \n %s \n\n\n " % (
            env, host_port, database, action_type, sql_content)
        process_id, next_step = run_manage.process_start(apply_process, process_type, finish_result, title,
                                                         display_content, env, process_template_id)
        # 存储内容等待流程完成时去执行
        sql_content = sql_content.replace("`", "")
        project_manage__work_order_process__run_manage_process_sql_content_co.insert_one({
            "process_id": process_id,
            "env": env,
            "host_port": host_port,
            "database": database,
            "action_type": action_type,
            "sql_content": sql_content,
        })
        run_manage.process_after_trigger(process_id, next_step)
        return {}
    except MyServiceException as e:
        return ResResult.return500(str(e))


def split_sql_content(sql_content):
    special_code_1 = "'"
    special_code_2 = '"'
    sql_item_list = []
    is_start_special = False
    special_code = None
    one_sql = ""
    sql_content = sql_content.strip()
    for index, item in enumerate(sql_content):
        if not special_code:
            if item == special_code_1:
                special_code = special_code_1
                is_start_special = True
            elif item == special_code_2:
                special_code = special_code_2
                is_start_special = True
            elif item == ";":
                sql_item_list.append(one_sql.strip())
                one_sql = ""
                continue
        else:
            if item == special_code and is_start_special:
                is_start_special = False
                special_code = None
        one_sql += item
        if index == len(sql_content) - 1 and one_sql != "":
            sql_item_list.append(one_sql.strip())

    return sql_item_list


def do_dumper(host, port, database, table, username, password, process_id):
    return mydumper_loader.do_dumper_in_remote(host, port, database, table, username, password, process_id)


def do_backup_table(host, port, database, sql_content, username, password, process_id):
    # mydumper_loader
    return ""


def exe_sql(basic_info):
    is_service_invoke_success = True
    print("basic_info", basic_info)
    env = basic_info["env"]
    host = basic_info["host"]
    port = basic_info["port"]
    username = basic_info["username"]
    password = basic_info["password"]
    database = basic_info["database"]
    action_type = basic_info["action_type"]
    sql_content = basic_info["sql_content"]
    process_id = basic_info["process_id"]
    try:
        execute_sql_log = ""
        is_exe_success = True
        if SQL_INVOKE_STR == action_type:
            # 使用inception执行并生成备份文件
            test_execute_sql_and_backup_result = my_inception.execute_sql(username, password, host, port, database,
                                                                          sql_content)
            inception_rollback_data = []
            for test_execute_sql_and_backup_result_item in test_execute_sql_and_backup_result:
                execute_sql_log += "执行SQL: " + test_execute_sql_and_backup_result_item["SQL"] + "<br/>"
                execute_sql_log += "执行结果: " + json.dumps(test_execute_sql_and_backup_result_item) + "<br/>"
                # 根据inception响应结果设置业务执行状态
                if test_execute_sql_and_backup_result_item.__contains__("errormessage") and \
                        test_execute_sql_and_backup_result_item["errormessage"] != "None":
                    is_service_invoke_success = False
                if "backup_dbname" in test_execute_sql_and_backup_result_item and \
                        test_execute_sql_and_backup_result_item[
                            "backup_dbname"] != "None":
                    backup_dbname = test_execute_sql_and_backup_result_item["backup_dbname"]
                    sequence = test_execute_sql_and_backup_result_item["sequence"]
                    sequence = sequence[1:len(sequence) - 1]
                    sql = test_execute_sql_and_backup_result_item["SQL"]
                    table_name = my_mysql.AnalysisSQl.get_table_name(sql)  # 分析SQL得到表名
                    # 获取回滚SQL
                    execute_sql_log += "生成备份SQL: <br/>"
                    try:
                        db_execute_result = my_inception.get_rollback_sql(backup_dbname, table_name, sequence)
                        rollback_sql = ""
                        for db_execute_result_item in db_execute_result:
                            sql = db_execute_result_item["rollback_statement"]
                            execute_sql_log += sql + "<br/>"
                            rollback_sql += sql + "\n"
                        inception_rollback_data_item = {
                            "backup_dbname": backup_dbname,
                            "backup_table_name": table_name,
                            "sequence": sequence,
                            "username": username,
                            "password": password,
                            "host": host,
                            "port": port,
                            "database": database,
                            "original_sql": sql,
                            "sql": rollback_sql,
                        }
                        inception_rollback_data.append(inception_rollback_data_item)
                    except Exception as e:
                        print(e)
                        execute_sql_log += "生成回滚异常: 详细原因为:" + str(e) + "<br/>"
                execute_sql_log += 100 * "-" + ": <br/>"
            # 记录回滚数据
            project_manage__work_order_process__run_manage_process_sql_content_rb_co.insert_one({
                "process_id": process_id,
                "env": env,
                "host": host,
                "port": port,
                "database": database,
                "action_type": action_type,
                "inception_rollback_data": inception_rollback_data
            })
        elif DB_AUTH_STR == action_type:
            try:
                test_execute_sql_and_backup_result = my_inception.execute_sql(username, password, host, port, database,
                                                                              sql_content,
                                                                              is_use_inception=False)
                execute_sql_log += "执行SQL: " + sql_content + "\n"
                execute_sql_log += "执行结果: " + json.dumps(test_execute_sql_and_backup_result) + "\n"
            except Exception as e:
                print(e)
                execute_sql_log += "执行顺便异常: 详细原因为:" + str(e) + "<br/>"
                is_service_invoke_success = False

        elif DANGER_SQL_STR == action_type:
            try:
                print("执行高危SQL")
                # 先生成备份
                table = my_mysql.AnalysisSQl.get_table_name(sql_content)
                dumper_dir_path, dumper_log_list = mydumper_loader.do_dumper_in_remote(host, port, database, table,
                                                                                       username,
                                                                                       password)
                do_dumper_log = "生成回滚语句的日志为: "
                for item in dumper_log_list:
                    do_dumper_log += item
                project_manage__work_order_process__run_manage_result_log_co.insert_one({
                    "process_id": process_id,
                    "log": do_dumper_log,
                    "is_exe_success": True,
                })
                inception_rollback_data = [
                    {
                        "username": username,
                        "password": password,
                        "host": host,
                        "port": port,
                        "database": database,
                        "dumper_dir_path": dumper_dir_path,
                    }
                ]
                project_manage__work_order_process__run_manage_process_sql_content_rb_co.insert_one({
                    "process_id": process_id,
                    "env": env,
                    "host": host,
                    "port": port,
                    "database": database,
                    "action_type": action_type,
                    "inception_rollback_data": inception_rollback_data
                })
                # 执行SQL
                test_execute_sql_and_backup_result = my_inception.execute_sql(username, password, host, port, database,
                                                                              sql_content,
                                                                              is_use_inception=False)
                execute_sql_log += "执行SQL: " + sql_content + "\n"
                execute_sql_log += "执行结果: " + json.dumps(test_execute_sql_and_backup_result) + "\n"
            except Exception as e:
                print(e)
                execute_sql_log += "执行顺便异常: 详细原因为:" + str(e) + "<br/>"
                is_service_invoke_success = False
        project_manage__work_order_process__run_manage_result_log_co.insert_one({
            "process_id": process_id,
            "log": execute_sql_log,
            "is_exe_success": is_exe_success,
        })
    except Exception as e:
        print(e)
        is_service_invoke_success = False
    # 修改状态
    run_manage.upgrade_process_service_invoke_status(process_id, is_service_invoke_success)


@app.route('/rollback_sql_invoke', methods=['POST'])
def rollback_sql_invoke():
    try:
        is_exe_success = True
        log = "开始回滚:"
        try:
            request_data = common_service.check_request_dat_not_null(
                ["process_instance_id"])
            if request_data.__contains__("is_rollback"):
                if request_data["is_rollback"]:
                    return
            process_instance_id = request_data["process_instance_id"]
            # 查询对应流程id的执行内容
            db_res_data = json.loads(
                dumps(project_manage__work_order_process__run_manage_process_sql_content_rb_co.find_one(
                    filter={'process_id': process_instance_id})))
            inception_rollback_data = db_res_data["inception_rollback_data"]
            action_type = db_res_data["action_type"]
            for inception_rollback_data_item in inception_rollback_data:
                username = inception_rollback_data_item["username"]
                password = inception_rollback_data_item["password"]
                host = inception_rollback_data_item["host"]
                port = inception_rollback_data_item["port"]
                database = inception_rollback_data_item["database"]
                if SQL_INVOKE_STR == action_type:
                    sql = inception_rollback_data_item["sql"]
                    db_execute_result_rollback = my_inception.execute_sql(username, password, host, port, database, sql,
                                                                          is_use_inception=False)
                    log += json.dumps(db_execute_result_rollback)
                elif DANGER_SQL_STR == action_type:
                    dumper_dir_path = inception_rollback_data_item["dumper_dir_path"]
                    loader_log_list = mydumper_loader.do_loader_in_remote(host, port, username, password,
                                                                          dumper_dir_path)
                    for loader_log_item in loader_log_list:
                        log += loader_log_item
                    log += "导入完成"
        except Exception as e:
            print(e)
            log += str(e)
            is_exe_success = False
        project_manage__work_order_process__run_manage_result_log_co.insert_one({
            "process_id": process_instance_id,
            "log": log,
            "is_exe_success": is_exe_success,
        })
        return {}
    except MyServiceException as e:
        print(e)
        return ResResult.return500(str(e))


@app.route('/finish_sql_invoke', methods=['POST'])
def finish_sql_invoke():
    try:
        request_data = common_service.check_request_dat_not_null(
            ["process_instance_id"])
        process_instance_id = request_data["process_instance_id"]
        # 查询对应流程id的执行内容
        db_res_data = json.loads(dumps(project_manage__work_order_process__run_manage_process_sql_content_co.find_one(
            filter={'process_id': process_instance_id})))
        env = db_res_data["env"]
        host_port = db_res_data["host_port"]
        database = db_res_data["database"]
        action_type = db_res_data["action_type"]
        sql_content = db_res_data["sql_content"]
        # 得到连接MySQL的信息
        query_result = json.loads(mysql.get_decrypt())
        query_result = query_result[0]

        level_mysql = query_result["mysql"]
        level_mysql_instance = level_mysql[env][host_port.replace(".", "_")]
        host = host_port.split(":")[0]
        port = host_port.split(":")[1]
        username = level_mysql_instance["username"]
        password = level_mysql_instance["password"]

        exe_sql_basic_info = {
            "env": env,
            "host": host,
            "port": port,

            "username": username,
            "password": password,

            "database": database,
            "action_type": action_type,
            "sql_content": sql_content,

            "process_id": process_instance_id,
        }
        # # 执行SQL
        project_manage__work_order_process__run_manage_result_log_co.insert_one({
            "process_id": process_instance_id,
            "log": "开始执行",
            "is_exe_success": True,
        })
        threading.Thread(target=exe_sql, args=[exe_sql_basic_info]).start()
        return {}
    except MyServiceException as e:
        print(e)
        return ResResult.return500(str(e))


def check_sql_executable(env, host_port, database, sql_content):
    query_result = json.loads(mysql.get_decrypt())
    query_result = query_result[0]
    level_mysql = query_result["mysql"]
    level_mysql_instance = level_mysql[env][host_port.replace(".", "_")]
    host = host_port.split(":")[0]
    port = host_port.split(":")[1]
    username = level_mysql_instance["username"]
    password = level_mysql_instance["password"]
    sql_content = sql_content.strip()
    if sql_content.endswith(";"):
        sql_content = sql_content[0:len(sql_content) - 1]
    check_execute_sql_result = my_inception.check_execute_sql(host, port, database, username, password, sql_content)
    is_check_ok = True
    error_message = ""
    for item in check_execute_sql_result:
        errormessage = item["errormessage"]
        upper_sql = item["SQL"].upper()
        if "ALTER " in upper_sql or "CREATE " in upper_sql:
            continue
        if errormessage != "None":
            is_check_ok = False
            error_message += "SQL语句: " + item["SQL"] + ": 的问题为" + errormessage + "<br/>"
    if not is_check_ok:
        raise MyServiceException("SQL检测失败,原因为: %s <br/>" % error_message)


RUNNING_STR = "RUNNING"


@app.route('/check_mysql_dumper', methods=['GET'])
def check_mysql_dumper():
    project_manage__work_order_process__run_manage_process_mysql_dumper_data_list = project_manage__work_order_process__run_manage_process_mysql_dumper_co.find(
        filter={
            "status": RUNNING_STR
        })
    for item in project_manage__work_order_process__run_manage_process_mysql_dumper_data_list:
        pass
