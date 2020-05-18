from component import my_mysqldump

test_sql_dict = {
    "delete": """
    delete from asset_manage__k8s_deploy_info where group_name = 'dev'
    """,
    "drop_table": """
    drop table asset_manage__k8s_conn_info
    """,
    "alter_table": """
ALTER TABLE `devops_platform`.`asset_manage__k8s_conn_info` 
ADD INDEX `group_name_index`(`group_name`)
""",
}


def test(host, port, database, username, password):
    """
    测试删除
    """
    # test_sql = test_sql_dict["delete"]
    # test_sql = test_sql_dict["drop_table"]
    test_sql = test_sql_dict["alter_table"]
    my_mysqldump.do_dump(host, port, database, username, password, test_sql)


if __name__ == '__main__':
    host = "192.168.71.96"
    port = "3306"
    database = "devops_platform"
    username = "root"
    password = "tristan123"
    test(host, port, database, username, password)
