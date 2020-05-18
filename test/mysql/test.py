from service.project_manage.associate_db import sql_work_order


def test():
    sql_content = """
delete from asset_manage__k8s_deploy_info where group_name = 'dev'
    """
    sql_item_list = sql_work_order.split_sql_content(sql_content)
    for item in sql_item_list:
        print( "item: ", item)


if __name__ == '__main__':
    test()
