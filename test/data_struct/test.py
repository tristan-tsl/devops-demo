import json

from component import my_data_struct2

moni_metadata = [
    {"pid": "", "id": "5", "name": "源码"},
    {"pid": "", "id": "6", "name": "源码"},
    {"pid": "5", "id": "5_1", "name": "SVN"},
    {"pid": "5", "id": "5_2", "name": "SVN"},
    {"pid": "5_1", "id": "5_1_1", "name": "测试"},
    {"pid": "5_1", "id": "5_1_2", "name": "测试"},

]
if __name__ == '__main__':
    tree_data = my_data_struct2.List.convert_to_tree(moni_metadata)
    print(json.dumps(tree_data))
