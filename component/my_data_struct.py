"""
数据结构类
"""


class List(object):
    @staticmethod
    def convert_to_tree(list_data):
        """
        固定树存储在list中的结构为:
            pid: 父id,默认为 ''
            id: id
            name: 名称
            env: 环境
            env_name: 环境名称

        注意: id 以 '_' 划分层级

        树的结构为:
        [
            {
                id: "环境",
                title: "环境名称",
                children: [
                    {
                        id: "资产类型id",
                        title:"资产类型名称",
                        children: [
                            {
                                id: "资产类型id",
                                title:"资产类型名称"
                                children: []
                            }
                        ]
                    }
                ]
            }


        ]
        """
        tree_data = []
        if not list_data or len(list_data) < 1:
            return tree_data
        for list_data_item in list_data:
            env = list_data_item["env"]
            env_name = list_data_item["env_name"]
            # 处理env层
            tree_data_level_env = None
            for tree_data_item in tree_data:
                if env == tree_data_item["id"]:
                    tree_data_level_env = tree_data_item
                    break
            if not tree_data_level_env:
                tree_data_level_env = {"id": env, "title": env_name, "children": []}
                tree_data.append(tree_data_level_env)
            # 处理资产管理类型层
            tree_data_level_data = tree_data_level_env["children"]
            pid = list_data_item["pid"]
            _id = list_data_item["id"]
            name = list_data_item["name"]
            if "" == pid:
                # 顶级结构
                tree_data_level_data.append({
                    "id": _id,
                    "title": name,
                    "children": []
                })
            else:
                # 下层结构
                # 为了提高解析速度,使用随机乱序填充数据
                tree_data_level_data_temp = tree_data_level_data
                pid_level = pid.split("_")
                pid_level_index = 0
                pid_middle = ""
                for pid_level_item in pid_level:
                    if pid_level_index != 0:
                        pid_middle += "_"
                    pid_middle += pid_level_item
                    pid_level_index += 1
                    for tree_data_level_data_item in tree_data_level_data_temp:
                        if tree_data_level_data_item["id"] == pid_middle:
                            tree_data_level_data_temp_temp = tree_data_level_data_item["children"]
                    if not tree_data_level_data_temp_temp:  # 创建多层的下层结构
                        tree_data_level_data_temp = tree_data_level_data_temp_temp
                for tree_data_level_data_temp_temp_item in tree_data_level_data_temp_temp:
                    if tree_data_level_data_temp_temp_item["id"] == pid_middle:
                        tree_data_level_data_temp_temp = tree_data_level_data_temp_temp_item["children"]
                tree_data_level_data_temp_temp.append(
                    {
                        "id": str(pid) + "_" + str((len(tree_data_level_data_temp) + 1)),
                        "title": name,
                        "children": []
                    }
                )
        return tree_data
