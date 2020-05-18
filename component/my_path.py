import os
import os.path


def get_path_tree(path, depth=0):
    res_result = ""
    if depth == 0:
        res_result += "\nroot:[" + path + "]\n"

    for item in os.listdir(path):
        res_result += "|      \t" * depth + "+--" + item + "\n"
        new_item = path + '/' + item
        if os.path.isdir(new_item):
            res_result += get_path_tree(new_item, depth + 1)
    return res_result


if __name__ == '__main__':
    print(get_path_tree("D:\projects\gitlab-local\project\code\Pass\devops-platform"))
