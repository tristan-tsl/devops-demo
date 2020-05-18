class List(object):
    @staticmethod
    def convert_to_tree(list_data):
        """
        id映射对象
        {
            "5":"源码",
            "5_1":"SVN",
            "5_1_1":"测试",
        }
        id树对象
        {
            "5":{
                "5_1":{
                    "5_1_1":{}
                }
            }
        }
        通过上面两个对象可以很快的直接生成树
        """
        id_mapping_obj = {}
        id_tree_obj = {}
        for list_data_item in list_data:
            _id = list_data_item["id"]
            name = list_data_item["name"]
            # id映射对象
            id_mapping_obj[_id] = name
            # id树对象
            id_part_arr = _id.split("_")
            id_init_str = ""
            id_tree_obj_cur_level = id_tree_obj
            for id_part_arr_index, id_part_arr_item in enumerate(id_part_arr):
                if id_part_arr_index != 0:
                    id_init_str += "_"
                id_init_str += id_part_arr_item
                if not id_tree_obj_cur_level.__contains__(id_init_str):
                    id_tree_obj_cur_level[id_init_str] = {}
                id_tree_obj_cur_level = id_tree_obj_cur_level[id_init_str]

        # 生成整合树
        def gen_display_tree(single_tree, res_result=None):
            if not res_result:
                res_result = []
            for key in single_tree:
                value = single_tree[key]
                res_result.append(
                    {
                        "id": key,
                        "title": id_mapping_obj[key],
                        "spread": True,
                        "children": gen_display_tree(value)
                    }
                )
            return res_result

        tree_data = gen_display_tree(id_tree_obj)
        return tree_data
