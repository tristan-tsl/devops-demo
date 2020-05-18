from builtins import print

from component import my_inception

username = "root"
password = "tristan123"
host = "192.168.71.96"
port = 3306
database = "devops_platform"

sql = """DELETE FROM test where 1=1 """
# sql = """INSERT INTO test (data_name) values('2');INSERT INTO test (data_name) values('3') """


if __name__ == '__main__':
    check_execute_sql_result = my_inception.check_execute_sql(host, port, database, username, password, sql)
    # print("check_execute_sql_result: ", check_execute_sql_result)
    for item in check_execute_sql_result:
        print(item)
