"""
基础语句-前缀:
mysqldump -P 3306 -h 192.168.71.96 -u root -ptristan123 devops_platform
基础语句-后缀:
> database.sql
导出数据库:
--lock-tables=false
导出数据库中的表:
asset_manage__k8s_deploy_info

导出数据库中的表的结构:
-d
asset_manage__k8s_deploy_info

按条件导出数据:
--set-gtid-purged=off --no-create-info  --skip-add-locks -t --where="group_name='dev'"
asset_manage__k8s_deploy_info
"""
import datetime
import os
import subprocess

import sqlparse
from sqlparse.tokens import Token

from config import project_root_path


class AnalysisResult(object):
    is_ddl: False
    is_delete_data: False
    identifier_name: None
    where_data: None

    def __init__(self):
        self.is_ddl = False
        self.is_delete_data = False
        self.identifier_name = None
        self.where_data = None


delete_data_str_list = ["delete", "drop", "truncate"]


def analysis_command_to_dump(sql):
    """
    分析导出命令
    """
    parse_results = sqlparse.parse(sql)
    parse_result = parse_results[0]
    tokens = parse_result.tokens
    analysis_result = AnalysisResult()
    for token in tokens:
        if token.ttype == Token.Text.Whitespace.Newline \
                or token.ttype == Token.Text.Whitespace:
            continue
        if token.ttype == Token.Keyword.DDL:
            analysis_result.is_ddl = True
            if token.value.lower() in delete_data_str_list:
                analysis_result.is_delete_data = True
        elif type(token) == sqlparse.sql.Identifier:
            analysis_result.identifier_name = token.value
        elif type(token) == sqlparse.sql.Where:
            analysis_result.where_data = token.value.replace("\n", "").strip()
    return analysis_result


def gen_dump_filename():
    basic_filename = datetime.datetime.now().strftime('%Y_%m_%d__%H_%M_%S') + ".sql"
    dir_name = os.path.join(project_root_path, "temp")
    if not os.path.exists(dir_name):
        os.mkdir(dir_name)
    dir_name = os.path.join(dir_name, "mysqldump")
    if not os.path.exists(dir_name):
        os.mkdir(dir_name)
    dump_filename = os.path.join(dir_name, basic_filename)
    return dump_filename


def get_do_dump_command(host, port, database, username, password, sql):
    """
    导出
    """
    # 组装执行的备份语句
    dump_command_basic_prefix = "mysqldump -P %s -h %s -u %s -p%s" % (
        port, host, username, password)
    dump_command = dump_command_basic_prefix  # 自动组装前缀
    dump_filename = gen_dump_filename()
    dump_command_basic_suffix = "> %s" % dump_filename  # 自动组装后缀
    target = database
    # 分析SQL
    if not sql.upper().strip().startswith("DELETE"):
        open(dump_filename, "w")
        return None, dump_filename
    analysis_result = analysis_command_to_dump(sql)
    identifier_name = analysis_result.identifier_name
    where_data = analysis_result.where_data
    # 组装
    if analysis_result.is_ddl:  # 如果是文档语句就需要对整体结构进行备份
        if not analysis_result.is_delete_data:
            dump_command_opt = "-d"
        else:
            dump_command_opt = ""
    else:
        dump_command_opt = "--set-gtid-purged=off --no-create-info  --skip-add-locks --skip-tz-utc "
        if where_data:
            where_data = where_data.strip()[len("where"):].strip()
            dump_command_opt += "--where=\"%s\"" % where_data
        target += " %s" % identifier_name
    dump_command += " %s %s %s" % (dump_command_opt, target, dump_command_basic_suffix)
    return dump_command, dump_filename


def do_dump(host, port, database, username, password, sql):
    dump_command, dump_filename = get_do_dump_command(host, port, database, username, password, sql)
    if not dump_command:
        return dump_filename
    print("dump_command: ", dump_command)
    p = subprocess.Popen(dump_command, shell=True, stdout=subprocess.PIPE)
    for line in p.stdout.readlines():
        print(line)
    return dump_filename


def do_dump_for_db_auth(sql):
    # 原始语句: GRANT SELECT ON `devops_platform`.* TO 'tristan_test'@'%'
    # 回滚语句: REVOKE SELECT ON devops_platform.* FROM 'tristan_test'@'%'
    sql.strip()
    original_sql = sql[len("GRANT"):]
    original_sql = original_sql.replace(" TO ", " FROM ")
    rollback_sql = "REVOKE " + original_sql
    dump_filepath = gen_dump_filename()
    with open(dump_filepath, "w") as dump_file:
        dump_file.write(rollback_sql)
    return dump_filepath


def do_import():
    """
    导入
    """
    pass


def do_dump_table_data(host, port, username, password, database, table_name):
    dump_file_path = ""
    return dump_file_path


def do_load_table_data(host, port, username, password, database, file_path):
    pass
