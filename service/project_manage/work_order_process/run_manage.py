import datetime
import json
import threading
import time

import requests
from bson.json_util import dumps
from bson.objectid import ObjectId
from flask import Blueprint, session, request

from common import common_service
from common.common_service import MyServiceException
from common.common_service import ResResult
from component import my_dingding
from component.my_mongo import mongodb
from config import app_conf
from service import user_manage
from service.project_manage.work_order_process import process_template

app = Blueprint('project_manage__work_order_process__run_manage', __name__,
                url_prefix='/project_manage/work_order_process/run_manage')

project_manage__work_order_process__run_manage_co = mongodb['project_manage__work_order_process__run_manage']
project_manage__work_order_process__run_manage_result_log_co = mongodb[
    'project_manage__work_order_process__run_manage_result_log']
project_manage__work_order_process__run_manage_process_template_co = mongodb[
    'project_manage__work_order_process__run_manage_process_template']
if not project_manage__work_order_process__run_manage_process_template_co.find_one():
    project_manage__work_order_process__run_manage_process_template_co.insert_one(
        {"process_template": "init", "value": "init -> init"})


@app.route('/list_log', methods=['POST'])
def list_log():
    try:
        request_data = common_service.check_request_dat_not_null(
            ["process_instance_id"])
        my_filter = {
            "process_id": request_data["process_instance_id"]
        }
        return dumps(project_manage__work_order_process__run_manage_result_log_co.find(filter=my_filter))
    except MyServiceException as e:
        return ResResult.return500(str(e))


@app.route('/list_process', methods=['POST'])
def list_process():
    my_filter = {}
    search_condition = []
    page_size = 9999999
    page_no = 1
    try:
        request_data = request.get_data()
        request_data = json.loads(request_data)
        search = request_data["search"]
        process_id = search["id"]
        if process_id:
            search_condition.append({"_id": ObjectId(process_id)})
        title = search["title"]
        if title:
            search_condition.append({"title": {'$regex': title}})
        service_type = search["service_type"]
        if service_type and "" != service_type:
            search_condition.append({"service_type": service_type})
        status = search["status"]
        if status and "" != status:
            search_condition.append({"status": status})
        service_invoke_status = search["service_invoke_status"]
        if service_invoke_status and "" != service_invoke_status:
            search_condition.append({"service_invoke_status": service_invoke_status})
        next_steps = search["next_steps"]
        if next_steps:
            search_condition.append({"next_steps": {'$regex': next_steps}})
        steps = search["steps"]
        if steps:
            search_condition.append({"steps": {'$regex': steps}})
        update_datetime = search["update_datetime"]
        if update_datetime and type(update_datetime) == list:
            update_datetime_start = update_datetime[0]
            update_datetime_end = update_datetime[1]
            if update_datetime_start and update_datetime_end:
                search_condition.append(
                    {"create_datetime": {
                        '$gte': datetime.datetime.strptime(update_datetime_start, '%Y-%m-%dT%H:%M:%S.%fZ')}})
                search_condition.append(
                    {"create_datetime": {
                        '$lte': datetime.datetime.strptime(update_datetime_end, '%Y-%m-%dT%H:%M:%S.%fZ')}})
        # 分页
        page = request_data["page"]
        if page["current"]:
            page_no = page["current"]
        if page["page_size"]:
            page_size = page["page_size"]
    except Exception as e:
        print(e)
    skip = page_size * (page_no - 1)
    if len(search_condition) > 0:
        my_filter = {"$and": search_condition}
    return dumps(
        {"data": project_manage__work_order_process__run_manage_co.find(filter=my_filter, sort=[("_id", -1)]).limit(
            page_size).skip(skip),
         "total": project_manage__work_order_process__run_manage_co.find(filter=my_filter, sort=[("_id", -1)]).limit(
             page_size).skip(skip).count()})


def do_request(request_data, process_instance_id):
    method = request_data["method"]
    url = request_data["url"]
    data = {
        "process_instance_id": process_instance_id
    }
    net_res_data = requests.request(method=method, url=url, json=data)
    if net_res_data.status_code != 200:
        raise MyServiceException("请求失败")
    print(net_res_data)


def exception_interrupt_resume(process_instance_id, db_res_data):
    try:
        do_request(db_res_data["finish_result"], process_instance_id)
    except Exception as e:
        print(e)
        raise MyServiceException("最终执行流程失败,请查询详细日志" + str(e))


def process_action_finish(process_instance_id, next_steps, db_res_data):
    cur_step, next_step, next_steps = do_next(next_steps)
    ready_to_finish = False
    if next_step == "":
        status = "FINISH"
        # 检查前置工单是否完成
        if "prepare_work_order_list" in db_res_data:
            prepare_work_order_list = db_res_data["prepare_work_order_list"]
            check_prepare_work_order_list_status(prepare_work_order_list)
        # 检查是否需要延迟执行
        if "special_invoke_datetime_duration" in db_res_data:
            special_invoke_datetime_duration = db_res_data["special_invoke_datetime_duration"]
            special_invoke_datetime_durations = special_invoke_datetime_duration.split("-")
            special_invoke_datetime_duration_start = special_invoke_datetime_durations[0]
            special_invoke_datetime_duration_end = special_invoke_datetime_durations[1]
            cur_datetime = datetime.datetime.now().strftime('%H:%M')
            if special_invoke_datetime_duration_start > cur_datetime or \
                    cur_datetime > special_invoke_datetime_duration_end:
                # 延迟执行
                status = "DELAY_INVOKE"
        if status == "FINISH":
            ready_to_finish = True
    else:
        status = "RUNNING"
    update_datetime = db_res_data["update_datetime"]
    convert_update_datetime = []
    for item in update_datetime:
        old_ts = str(item["$date"])
        dt1 = datetime.datetime.utcfromtimestamp(float(old_ts) / 10 ** (len(old_ts) - 10))
        convert_update_datetime.append(dt1)
    convert_update_datetime.append(datetime.datetime.utcnow())
    process_instance = {
        "next_step": next_step,
        "next_steps": next_steps,
        "status": status,
        "update_datetime": convert_update_datetime,
        "service_invoke_status": "INVOKING"
    }
    project_manage__work_order_process__run_manage_co.update_one(filter={'_id': ObjectId(process_instance_id)},
                                                                 update={'$set': process_instance})
    if ready_to_finish:
        try:
            do_request(db_res_data["finish_result"], process_instance_id)
        except Exception as e:
            print(e)
            raise MyServiceException("最终执行流程失败,请查询详细日志" + str(e))
    if status == "DELAY_INVOKE":
        create_delay_invoke_thread(process_instance_id)
    process_after_trigger(process_instance_id, next_step)


def process_action_reject(process_instance_id, reject_reason):
    process_instance = {
        "status": "REJECT",
        "reject_reason": reject_reason
    }
    project_manage__work_order_process__run_manage_co.update_one(filter={'_id': ObjectId(process_instance_id)},
                                                                 update={'$set': process_instance})


def process_action_destroy(process_instance_id):
    process_instance = {
        "status": "DESTROY"
    }
    project_manage__work_order_process__run_manage_co.update_one(filter={'_id': ObjectId(process_instance_id)},
                                                                 update={'$set': process_instance})


rollback_service_type_only_list = ["schedule_manage", "project_deploy"]


def process_action_rollback(process_instance_id, db_res_data):
    if db_res_data["service_type"] in rollback_service_type_only_list:
        db_res_data_query = json.loads(dumps(project_manage__work_order_process__run_manage_co.find_one(
            filter={
                'service_type': db_res_data["service_type"],
                'system_tag': db_res_data["system_tag"],
                'status': 'FINISH',
            },
            sort=[("_id", -1)]
        )))
        if db_res_data_query["_id"]["$oid"] != process_instance_id:
            project_manage__work_order_process__run_manage_co.update_one(filter={'_id': ObjectId(process_instance_id)},
                                                                         update={'$set': {
                                                                             "is_rollback": True
                                                                         }})
            raise MyServiceException("当前系统有新的工单,无法回滚老的工单")
    method = db_res_data["finish_result"]["method"]
    rb_url = db_res_data["finish_result"]["rb_url"]
    update_datetime = db_res_data["update_datetime"]
    convert_update_datetime = []
    for item in update_datetime:
        old_ts = str(item["$date"])
        dt1 = datetime.datetime.utcfromtimestamp(float(old_ts) / 10 ** (len(old_ts) - 10))
        convert_update_datetime.append(dt1)
    convert_update_datetime.append(datetime.datetime.utcnow())
    try:
        do_request({"method": method, "url": rb_url}, process_instance_id)
        process_instance = {
            "is_rollback": True,
            "update_datetime": convert_update_datetime,
        }
        project_manage__work_order_process__run_manage_co.update_one(filter={'_id': ObjectId(process_instance_id)},
                                                                     update={'$set': process_instance})
    except Exception as e:
        print(e)
        raise MyServiceException("回滚流程失败" + str(e))


def get_first_step(steps):
    steps = steps.strip()
    index = steps.find(">")
    if index < 0:
        index = len(steps)
    return steps[0:index].strip()


def get_last_step(steps):
    steps = steps.strip()
    index = steps.rfind(">") + len(">")
    if index < 0:
        index = 0
    return steps[index:].strip()


@app.route('/process_action', methods=['PUT'])
def process_action():
    try:
        request_data = common_service.check_request_dat_not_null(
            ["process_instance_id", "action"])
        cur_user_id = session.get("user_id")
        process_instance_id = request_data["process_instance_id"]
        action = request_data["action"]  # 动作
        is_need_destroy_child_process = False
        # 查询流程
        db_res_data = json.loads(dumps(project_manage__work_order_process__run_manage_co.find_one(
            filter={'_id': ObjectId(process_instance_id)})))
        if action == "FINISH":  # 跳转到下一个步骤
            # 流程的当前节点必须要是当前登录人
            del db_res_data["_id"]
            next_step = db_res_data["next_step"]
            next_steps = db_res_data["next_steps"]
            if next_step != "*" and next_step != cur_user_id:
                raise MyServiceException("当前登录人(%s)没有权限操作流程(%s)" % (cur_user_id, process_instance_id))

            process_action_finish(process_instance_id, next_steps, db_res_data)
        elif action == "REJECT":  # 驳回流程
            reject_reason = request_data["reject_reason"]  # 驳回理由
            print("reject_reason: ", reject_reason)
            next_steps = db_res_data["next_steps"]
            do_next(next_steps)
            process_action_reject(process_instance_id, reject_reason)
            is_need_destroy_child_process = True
        elif action == "DESTROY":  # 销毁流程
            next_steps = db_res_data["next_steps"]
            if next_steps != "":
                do_next(next_steps)
            else:
                is_cur_user_process(get_last_step(db_res_data["steps"]))
            process_action_destroy(process_instance_id)
            is_need_destroy_child_process = True
        elif action == "ROLLBACK":  # 回滚流程
            last_step = get_last_step(db_res_data["steps"])
            if last_step != "*" and last_step != cur_user_id:
                raise MyServiceException("当前登录人(%s)没有权限操作流程(%s)" % (cur_user_id, process_instance_id))
            process_action_rollback(process_instance_id, db_res_data)
            is_need_destroy_child_process = True
        elif action == "SPECIAL_INVOKE_DATETIME_DURATION":  # 指定执行时间段
            # 流程的当前节点必须要是当前登录人
            next_steps = db_res_data["next_steps"]
            if next_steps == "":
                is_cur_user_process(get_last_step(db_res_data["steps"]))
            else:
                next_step = db_res_data["next_step"]
                if next_step != "*" and next_step != cur_user_id:
                    raise MyServiceException("当前登录人(%s)没有权限操作流程(%s)" % (cur_user_id, process_instance_id))
            special_invoke_datetime_duration = request_data["special_invoke_datetime_duration"]
            special_invoke_datetime_duration_str = "-".join(special_invoke_datetime_duration)
            do_special_invoke_datetime_duration(process_instance_id, special_invoke_datetime_duration_str)
        elif action == "EXCEPTION_INTERRUPT_RESUME":  # 异常中断恢复
            is_cur_user_process(get_last_step(db_res_data["steps"]))
            exception_interrupt_resume(process_instance_id, db_res_data)
        #
        #
        #
        # 处理以当前工单为前置流程的工单
        if is_need_destroy_child_process:
            db_res_data_child_process = json.loads(dumps(project_manage__work_order_process__run_manage_co.find(
                filter={'prepare_work_order_list': {
                    "$regex": process_instance_id
                }})))
            for item in db_res_data_child_process:
                project_manage__work_order_process__run_manage_co.delete_one(
                    filter={'_id': ObjectId(item["_id"]["$oid"])})
        return {}
    except MyServiceException as e:
        print(e)
        return ResResult.return500(str(e))


def do_special_invoke_datetime_duration(process_id, special_invoke_datetime_duration):
    project_manage__work_order_process__run_manage_co.update_one(filter={'_id': ObjectId(process_id)},
                                                                 update={'$set': {
                                                                     "special_invoke_datetime_duration":
                                                                         special_invoke_datetime_duration
                                                                 }})


def is_cur_user_process(cur_step):
    cur_user_id = session.get("user_id")
    if cur_step not in ["*", cur_user_id]:
        raise MyServiceException("你不是当前流程的指定人")


def do_next(process_steps, level=1):
    process_steps = process_steps.strip()
    if not process_steps or len(process_steps) < 1:
        raise MyServiceException("流程(%s)不能为空" % process_steps)

    # 计算cur_step、next_step、next_steps
    first_step_sep_index = process_steps.find(">")
    next_steps = ""
    next_step = ""
    # 剩余节点
    if first_step_sep_index <= 0:
        cur_step = process_steps
    else:
        cur_step = process_steps[0:first_step_sep_index].strip()
        if level != 0:
            next_steps = process_steps[first_step_sep_index + 1:].strip()
            try:
                cur_step_temp, next_step_temp, next_steps_temp = do_next(next_steps, level=0)
                next_step = cur_step_temp
            except MyServiceException as e:
                print(e)
    if level != 0:
        is_cur_user_process(cur_step)
    return cur_step, next_step, next_steps


def process_start(process_steps, service_type, finish_result, title, display_content, env, process_template_id,
                  prepare_work_order_list=None, system_tag=""):
    """
    修正: 启动流程只是启动历程而不会去执行流程
    """
    # 校验流程是否符合流程模板
    process_template.check_input_process_in_process_template(process_steps, env, process_template_id)
    #     # 校验入参
    check_prepare_work_order_list_exists(prepare_work_order_list)
    cur_step, next_step, next_steps = do_next(process_steps)
    cur_datetime = datetime.datetime.utcnow()
    status = "RUNNING"
    process_instance = {
        "title": title,
        "prepare_work_order_list": prepare_work_order_list,
        "system_tag": system_tag,
        "display_content": display_content,
        "steps": process_steps,
        # 流程
        "next_step": cur_step,
        "next_steps": process_steps,
        # 状态
        "status": status,
        "service_invoke_status": "",
        # 完结之后的跳转地址及请求方式
        "finish_result": finish_result,
        # 业务类型,用于搜索分类
        "service_type": service_type,
        "create_datetime": cur_datetime,
        "update_datetime": [cur_datetime],
    }
    db_result = project_manage__work_order_process__run_manage_co.insert_one(process_instance)
    insert_id = json.loads(dumps(db_result.inserted_id))["$oid"]
    return insert_id, cur_step


def parse_prepare_work_order_list(prepare_work_order_list):
    if not prepare_work_order_list:
        return []
    prepare_work_order_list = prepare_work_order_list.strip()
    return prepare_work_order_list.split(";")


def check_prepare_work_order_list_exists(prepare_work_order_list):
    prepare_work_order_lists = parse_prepare_work_order_list(prepare_work_order_list)
    for item in prepare_work_order_lists:
        try:
            db_res_data = json.loads(dumps(project_manage__work_order_process__run_manage_co.find_one(
                filter={'_id': ObjectId(item)})))
            if not db_res_data:
                raise MyServiceException("该前置流程不存在(%s)" % item)
        except Exception as e:
            print(e)
            raise MyServiceException("该前置流程不存在(%s) e:%s" % (item, str(e)))


def check_prepare_work_order_list_status(prepare_work_order_list):
    prepare_work_order_lists = parse_prepare_work_order_list(prepare_work_order_list)
    for item in prepare_work_order_lists:
        try:
            db_res_data = json.loads(dumps(project_manage__work_order_process__run_manage_co.find_one(
                filter={'_id': ObjectId(item)})))
            if db_res_data["status"] != "FINISH":
                raise MyServiceException("该前置流程未完成(%s)" % item)
        except Exception as e:
            print(e)
            raise MyServiceException("该前置流程未完成(%s) e:%s" % (item, str(e)))


base_url = app_conf["project"]["pubic_url"] + "/project_manage/work_order_process/run_manage.html?process_id="


def process_after_trigger(process_id, user_id, msg=None):
    if not user_id or user_id == "":
        return
    if not msg:
        msg = "有你的审核流程,请注意接收:  "
    msg += base_url
    msg += process_id
    push_msg_to_ding(msg, user_id)


def push_msg_to_ding(msg, user_id):
    # 获取当前用户的ding id
    ding_id = user_manage.get_cur_ding_id(user_id)
    # 推送钉钉机器人消息
    my_dingding.send_msg(msg, ding_id)


@app.route('/check_process_delay_invoke', methods=['GET'])
def check_process_delay_invoke():
    query_result = project_manage__work_order_process__run_manage_co.find(filter={
        "status": "DELAY_INVOKE"
    })
    query_result_data = json.loads(dumps(query_result))
    for process_record in query_result_data:
        if "special_invoke_datetime_duration" not in process_record:
            continue
        # 执行流程
        create_delay_invoke_thread(process_record["_id"]["$oid"])
    return {}


def do_delay_invoke(process_id):
    while True:
        try:
            db_res_data = json.loads(dumps(project_manage__work_order_process__run_manage_co.find_one(
                filter={'_id': ObjectId(process_id), "status": "DELAY_INVOKE"})))
            special_invoke_datetime_duration = db_res_data["special_invoke_datetime_duration"]
            special_invoke_datetime_durations = special_invoke_datetime_duration.split("-")
            special_invoke_datetime_duration_start = special_invoke_datetime_durations[0]
            special_invoke_datetime_duration_end = special_invoke_datetime_durations[1]
            cur_datetime = datetime.datetime.now().strftime('%H:%M')
            if special_invoke_datetime_duration_start < cur_datetime < special_invoke_datetime_duration_end:
                do_request(db_res_data["finish_result"], process_id)
                status = "FINISH"
                update_datetime = db_res_data["update_datetime"]
                convert_update_datetime = []
                for item in update_datetime:
                    old_ts = str(item["$date"])
                    dt1 = datetime.datetime.utcfromtimestamp(float(old_ts) / 10 ** (len(old_ts) - 10))
                    convert_update_datetime.append(dt1)
                convert_update_datetime.append(datetime.datetime.utcnow())
                process_instance = {
                    "next_step": "",
                    "next_steps": "",
                    "status": status,
                    "update_datetime": convert_update_datetime,
                }
                project_manage__work_order_process__run_manage_co.update_one(
                    filter={'_id': ObjectId(process_id)},
                    update={'$set': process_instance})
                return
            time.sleep(60)  # 定时检测
        except Exception as e:
            print(e)


def create_delay_invoke_thread(process_id):
    threading.Thread(target=do_delay_invoke, args=[process_id],
                     name='do_delay_invoke').start()


def upgrade_process_service_invoke_status(process_id, is_service_invoke_success):
    if is_service_invoke_success:
        service_invoke_success = "SUCCESS"
        service_invoke_success_str = "成功"
    else:
        service_invoke_success = "FAILURE"
        service_invoke_success_str = "失败"
    process_instance = {
        "service_invoke_status": service_invoke_success,
    }
    project_manage__work_order_process__run_manage_co.update_one(
        filter={'_id': ObjectId(process_id)},
        update={'$set': process_instance})
    # 获取该流程的第一个人
    db_result = json.loads(
        dumps(project_manage__work_order_process__run_manage_co.find_one(filter={'_id': ObjectId(process_id)})))
    steps = db_result["steps"]
    process_first_user = get_first_step(steps)
    process_after_trigger(process_id, process_first_user, msg="您的工单执行%s了,请注意查看" % service_invoke_success_str)
