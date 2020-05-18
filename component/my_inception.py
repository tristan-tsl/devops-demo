"""
https://qunarcorp.github.io/inception/backup/

"""
import MySQLdb

from config import app_conf

inception_host = app_conf["inception"]["host"]
inception_port = app_conf["inception"]["port"]
inception_backup_host = app_conf["inception"]["backup"]["host"]
inception_backup_port = app_conf["inception"]["backup"]["port"]
inception_backup_username = app_conf["inception"]["backup"]["username"]
inception_backup_password = app_conf["inception"]["backup"]["password"]


def gen_inception_check_execute_sql(user, password, host, port, database, sql):
    return """
        /*--user=%s;--password=%s;--enable-check;--host=%s;--port=%s;*/
        inception_magic_start;
        use %s;
        %s;
        inception_magic_commit;
    """ % (user, password, host, port, database, sql)


def check_execute_sql(host, port, database, username, password, sql):
    db_execute_result = []
    inception_check_execute_sql = gen_inception_check_execute_sql(username, password, host, port, database, sql)
    host = inception_host
    port = inception_port
    username = ""
    password = ""
    database = ""
    conn = MySQLdb.connect(host=host, user=username, passwd=password, db=database, port=port, charset='utf8')
    cur = conn.cursor()
    cur.execute(inception_check_execute_sql)
    field_names = [i[0] for i in cur.description]
    result = cur.fetchall()
    for row in result:
        db_execute_result_item = {}
        for field_name_index, field_name in enumerate(field_names):
            db_execute_result_item[field_name] = row[field_name_index]
        db_execute_result.append(db_execute_result_item)
    cur.close()
    conn.close()
    return db_execute_result


def gen_inception_execute_sql(user, password, host, port, database, sql):
    return """
        /*--user=%s;--password=%s;--host=%s;--enable-execute;--enable-ignore-warnings;--port=%s;*/
        inception_magic_start;
        use %s;
        %s;
        inception_magic_commit;
    """ % (user, password, host, port, database, sql)


def execute_sql(user, password, host, port, database, sql, is_use_inception=True):
    port = int(port)
    sql = sql.replace("`", "")
    sql = sql.strip()
    if sql.endswith(";"):
        sql = sql[0:len(sql) - 1]
    print("user:", user, "password:", password, "port:", port, "database:", database, "sql:", sql, "is_use_inception:",
          is_use_inception)
    db_execute_result = []
    inception_execute_sql_result = sql
    if is_use_inception:
        inception_execute_sql_result = gen_inception_execute_sql(user, password, host, port, database, sql)
        host = inception_host
        user = ""
        password = ""
        database = ""
        port = inception_port
    # 捕获异常为: MySQLdb.Error as e:  e.args[0], e.args[1]
    conn = MySQLdb.connect(host=host, user=user, passwd=password, db=database, port=port, charset='utf8',
                           autocommit=True)
    cur = conn.cursor()
    rows_affected = cur.execute(inception_execute_sql_result)
    if cur.description is None:
        return [{"rows_affected": rows_affected}]
    field_names = [i[0] for i in cur.description]
    result = cur.fetchall()
    for row in result:
        db_execute_result_item = {}
        for field_name_index, field_name in enumerate(field_names):
            db_execute_result_item[field_name] = row[field_name_index]
        db_execute_result.append(db_execute_result_item)
    cur.close()
    conn.close()
    return db_execute_result


def get_rollback_sql(backup_dbname, backup_table_name, sequence):
    inception_query_rollback_sql = """ select rollback_statement from %s.%s where opid_time ='%s' """ % (
        backup_dbname, backup_table_name, sequence)
    db_execute_result = execute_sql(inception_backup_username, inception_backup_password, inception_backup_host,
                                    inception_backup_port, "",
                                    inception_query_rollback_sql, is_use_inception=False)
    return db_execute_result
