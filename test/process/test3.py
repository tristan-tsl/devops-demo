moni_data = [
    [{"openid": "test1"}, {"openid": "test2"}],
    [{"openid": "test12"}, {"openid": "test23"}],
    [{"openid": "test123"}, {"openid": "test234"}],
    [{"openid": "test1234"}, {"openid": "test2345"}],
]


def gen_process_step_str(process_steps):
    last_level_data = []
    for index, item_role in enumerate(process_steps):
        if index == 0:
            convert_item_roles = []
            for convert_item_role in item_role:
                convert_item_roles.append(convert_item_role["openid"])
            last_level_data = convert_item_roles
            continue
        last_level_data_temp = []
        for item_user in item_role:
            for item_last_user in last_level_data:
                last_level_data_temp.append(item_user["openid"] + " > " + item_last_user)
        last_level_data = last_level_data_temp
    return last_level_data


if __name__ == '__main__':
    moni_data_result = gen_process_step_str(moni_data)
    for item in moni_data_result:
        print("item: ", item)
    # print("moni_data_result: ", moni_data_result)
    #
    "test12 > test1"
    "test12 > test2"
    "test23 > test1"
    "test23 > test2"
    #
    "test123 > test12 > test1"
    "test123 > test12 > test2"
    "test123 > test23 > test1"
    "test123 > test23 > test2"
    "test234 > test12 > test1"
    "test234 > test12 > test2"
    "test234 > test23 > test1"
    "test234 > test23 > test2"
    pass
