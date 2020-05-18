import time
from builtins import print

from component import my_inception
from component import my_mysql

user = "root"
password = "tristan123"
host = "192.168.71.96"
port = 3306
database = "devops_platform"

"""
不支持的SQL类型:
TRUNCATE
DROP

"""


def test_execute_sql_and_backup():
    sql = """DELETE FROM test  """
    sql = """INSERT INTO test (data_name) values('2');INSERT INTO test (data_name) values('3') """
    # sql = """UPDATE test SET data_name='999' WHERE id=1 """
    # sql = """ALTER TABLE test ADD data_age int NOT NUll DEFAULT 20 COMMENT '年龄' """
    # 执行
    execute_sql_result = my_inception.execute_sql(user, password, host, port, database, sql)
    print(execute_sql_result)
    return execute_sql_result


def test_rollback(backup_dbname=None, backup_table_name=None, sequence=None):
    # 获取回滚的语句
    if not backup_dbname:
        backup_dbname = "192_168_71_96_3306_devops_platform"
    if not backup_table_name:
        backup_table_name = "test"
    if not sequence:
        sequence = "1569045088_714_0"
    db_execute_result = my_inception.get_rollback_sql(backup_dbname, backup_table_name, sequence)
    print(db_execute_result)
    # 执行回滚的语句
    for db_execute_result_item in db_execute_result:
        sql = db_execute_result_item["rollback_statement"]
        db_execute_result_rollback = my_inception.execute_sql(user, password, host, port, database, sql,
                                                              is_use_inception=False)
        print(db_execute_result_rollback)


error_execute_result = ["Execute Successfully", "Execute Successfully\nBackup successfully"]

if __name__ == '__main__':
    test_execute_sql_and_backup_result = test_execute_sql_and_backup()
    for test_execute_sql_and_backup_result_item in test_execute_sql_and_backup_result:
        print(test_execute_sql_and_backup_result_item)
        if "backup_dbname" in test_execute_sql_and_backup_result_item and test_execute_sql_and_backup_result_item[
            "backup_dbname"] != "None":
            affected_rows = test_execute_sql_and_backup_result_item["Affected_rows"]
            backup_dbname = test_execute_sql_and_backup_result_item["backup_dbname"]
            sequence = test_execute_sql_and_backup_result_item["sequence"]
            sequence = sequence[1:len(sequence) - 1]
            sql = test_execute_sql_and_backup_result_item["SQL"]
            # 分析SQL得到表名
            table_name = my_mysql.AnalysisSQl.get_table_name(sql)
            print("backup_dbname:", backup_dbname, "sequence:", sequence, "table_name:", table_name)
            print("延迟5S测试回滚")
            time.sleep(5)
            test_rollback(backup_dbname, table_name, sequence)
