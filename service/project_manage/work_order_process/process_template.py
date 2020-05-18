import json

from bson.json_util import dumps
from flask import Blueprint, session

from common import common_service
from component.my_mongo import mongodb
from service import access_control

app = Blueprint('project_manage__work_order_process__process_template', __name__,
                url_prefix='/project_manage/work_order_process/process_template')

project_manage__work_order_process__process_template_co = mongodb[
    'project_manage__work_order_process__process_template']
if not project_manage__work_order_process__process_template_co.find_one():
    project_manage__work_order_process__process_template_co.insert_one({"process_template": {}, })


@app.route('/get', methods=['GET'])
def get():
    return common_service.query(project_manage__work_order_process__process_template_co)


@app.route('/put', methods=['PUT'])
def put():
    return common_service.insert(project_manage__work_order_process__process_template_co)


@app.route('/get_process_template_role', methods=['POST'])
def get_process_template_role():
    try:
        request_data = common_service.check_request_dat_not_null(["process_template_id"])
        env = request_data["env"]
        process_template_id = request_data["process_template_id"]
        # 获取该模板对应的值
        process_template_level_top = json.loads(get())
        process_template_level_second = process_template_level_top[0]
        process_template_level_data = process_template_level_second["process_template"]
        if not process_template_level_data.__contains__(env):
            raise common_service.MyServiceException("该流程模板环境(%s)不存在" % env)
        process_template_level_env = process_template_level_data[env]
        if not process_template_level_env.__contains__(process_template_id):
            raise common_service.MyServiceException("该流程模板id(%s)不存在" % process_template_id)
        process_template = process_template_level_env[process_template_id]
        process_template = process_template.strip()
        if not process_template or process_template.strip() == "":
            raise common_service.MyServiceException("该流程模板值为空")
        return process_template
    except common_service.MyServiceException as e:
        print(e)
        return common_service.ResResult.return500(str(e))


SPECIAL_ALLOW_STR = '*'


def do_get_process_template(env, process_template_id):
    # 获取该模板对应的值
    process_template_level_top = json.loads(get())
    process_template_level_second = process_template_level_top[0]
    process_template_level_data = process_template_level_second["process_template"]
    if not process_template_level_data.__contains__(env):
        raise common_service.MyServiceException("该流程模板环境(%s)不存在" % env)
    process_template_level_env = process_template_level_data[env]
    if not process_template_level_env.__contains__(process_template_id):
        raise common_service.MyServiceException("该流程模板id(%s)不存在" % process_template_id)
    process_template = process_template_level_env[process_template_id]
    process_template = process_template.strip()
    if not process_template or process_template.strip() == "":
        raise common_service.MyServiceException("该流程模板值为空")
    # 当前登录的用户
    cur_user_id = session.get("user_id")
    # 生成流程
    process_template_list = process_template.split(">")
    # 为方便使用,倒序
    process_template_list = list(reversed(process_template_list))
    res_result = []
    is_already_in_process = False
    # 当前登录人的产品标签
    cur_user_label_list = access_control.get_user_label_list(cur_user_id)
    for index, item in enumerate(process_template_list):
        if is_already_in_process:
            break
        res_result_item = []
        item = item.strip()
        group_struct_has_user = json.loads(access_control.get_group_struct_has_user(item))

        # 判断该角色是否包含当前登录人
        for group_struct_has_user_index, group_struct_has_user_item in enumerate(group_struct_has_user):
            user_nick = group_struct_has_user_item["nick"]
            user_label = group_struct_has_user_item["label"]
            user_open_id = group_struct_has_user_item["user_open_id"]
            if cur_user_id == user_open_id:
                is_already_in_process = True
                res_result_item = [{"openid": user_open_id, "nick": user_nick}]
                break
            else:
                # 流程开始的第一个人必须是当前登录人
                if index == len(process_template_list) - 1 and group_struct_has_user_index == len(
                        group_struct_has_user) - 1:
                    raise common_service.MyServiceException("流程开始的第一个人必须是当前登录人")
                if SPECIAL_ALLOW_STR not in user_label:
                    if len(cur_user_label_list) != len(user_label):
                        continue
                    for cur_user_label_list_item in cur_user_label_list:
                        if cur_user_label_list_item not in user_label:
                            continue
                res_result_item.append({"openid": user_open_id, "nick": user_nick})
        # 判断流程是否至少有一个人
        if len(res_result_item) < 1:
            raise common_service.MyServiceException("当前用户拥有的流程在 %s 流程节点上 没有一个人" % item)
        res_result.append(res_result_item)
        if is_already_in_process:
            continue
    # 判断整体流程至少含有一个人
    if len(res_result) < 1:
        raise common_service.MyServiceException("当前登录人所需要的流程至少需要一个人")
    return res_result


@app.route('/get_my_process', methods=['POST'])
def get_process_template():
    """
    约束: 返回的流程必须包含当前用户，
     且流程运行时的第一个人必须为当前登录人,
      流程至少包含一个角色,
       如果当前在整组流程中有更高级别的角色则会导致流程长度缩减(不会显示低级别的角色)
    :return:
    """
    try:
        request_data = common_service.check_request_dat_not_null(["process_template_id", "env"])
        env = request_data["env"]
        process_template_id = request_data["process_template_id"]
        return dumps(do_get_process_template(env, process_template_id))
    except common_service.MyServiceException as e:
        print(e)
        return common_service.ResResult.return500(str(e))


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


def check_input_process_in_process_template(input_process, env, process_template_id):
    process_template_data = do_get_process_template(env, process_template_id)
    all_process = gen_process_step_str(process_template_data)
    if input_process not in all_process:
        raise common_service.MyServiceException("非法入侵,非法流程")
