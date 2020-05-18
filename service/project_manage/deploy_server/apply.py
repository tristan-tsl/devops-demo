import glob
import json
import os
import threading

from bson.json_util import dumps
from flask import Blueprint

from common import common_service
from common.common_service import MyServiceException
from common.common_service import ResResult
from component import my_path
from component.my_archive import MyArchive
from component.my_jenkins import MyJenkins
from component.my_k8s import MyK8s
from component.my_mongo import mongodb
from component.my_svn import MySVN
from service.asset_manage.code_server import svn
from service.asset_manage.deploy_server import jenkins
from service.project_manage.work_order_process import run_manage
from . import template

app = Blueprint('project_manage__deploy_server__apply', __name__,
                url_prefix='/project_manage/deploy_server/apply')

asset_manage__deploy_server__k8s_co = mongodb['asset_manage__deploy_server__k8s']
project_manage__deploy_server__apply_record_co = mongodb['project_manage__deploy_server__apply_record']
project_manage__work_order_process__run_manage_process_project_deploy_co = mongodb[
    'project_manage__work_order_process__run_manage_process_project_deploy']
project_manage__work_order_process__run_manage_result_log_co = mongodb[
    'project_manage__work_order_process__run_manage_result_log']
project_manage__work_order_process__run_manage_process_process_project_rb_co = mongodb[
    'project_manage__work_order_process__run_manage_process_process_project_rb']


def deploy_java(request_data):
    process_id = request_data["process_id"]
    project_type = request_data["project_type"]
    deploy_env = request_data["deploy_env"]
    data_namespace = request_data["namespace"]
    data_image_id = request_data["image_id"]
    deploy_name = request_data["deploy_name"]

    # 转换项目名为部署名
    project_manage__work_order_process__run_manage_result_log_co.insert_one({
        "process_id": process_id,
        "log": "开始部署",
        "is_exe_success": True,
    })
    # 获取k8s连接信息
    asset_manage__deploy_server__k8s_co_one = json.loads(common_service.query(asset_manage__deploy_server__k8s_co))[
        0]
    data_k8s = asset_manage__deploy_server__k8s_co_one["k8s"]
    data_k8s_env = data_k8s[deploy_env]
    data_k8s_host = data_k8s_env["host"]
    data_k8s_token = data_k8s_env["token"]

    # 更新k8s镜像
    try:
        my_k8s = MyK8s(data_k8s_host, data_k8s_token)
        cur_image_id = my_k8s.get_cur_image_id(data_namespace, deploy_name)
        # 生成回滚
        # 查询k8s当前镜像版本
        project_manage__work_order_process__run_manage_process_process_project_rb_co.insert_one({
            "process_id": process_id,
            "project_type": project_type,
            "deploy_env": deploy_env,
            "data_namespace": data_namespace,
            "data_image_id": cur_image_id,
            "deploy_name": deploy_name,
        })
        project_manage__work_order_process__run_manage_result_log_co.insert_one({
            "process_id": process_id,
            "log": "已经为回滚做好准备",
            "is_exe_success": True,
        })
        my_k8s.update_image(data_namespace, deploy_name, data_image_id)
        project_manage__work_order_process__run_manage_result_log_co.insert_one({
            "process_id": process_id,
            "log": "部署成功",
            "is_exe_success": True,
        })
        run_manage.upgrade_process_service_invoke_status(process_id, True)
    except Exception as e:
        print(e)
        project_manage__work_order_process__run_manage_result_log_co.insert_one({
            "process_id": process_id,
            "log": "部署失败" + str(e),
            "is_exe_success": True,
        })
        run_manage.upgrade_process_service_invoke_status(process_id, False)
        raise e


def check_php_url_tag_package(url, svn_server_host):
    url_prefix = url[0:len(svn_server_host)]
    if url_prefix != svn_server_host:
        raise MyServiceException("检查: " + url + " 时发现文件地址不为允许的svn服务器地址")
    # suffix_is_ok = False
    # if url.endswith(".zip"):
    #     suffix_is_ok = True
    # if not suffix_is_ok:
    #     raise MyServiceException("检查: " + url + " 文件后缀只能为.zip")


def check_php_tag_package_standard(svn_tag_package_list_item, check_php_tag_package_path, forbid_dir_list):
    """
    :param svn_tag_package_list_item:
    :param check_php_tag_package_path:
    :param forbid_dir_list:
    :return:
    """
    last_index = check_php_tag_package_path.rfind(".")
    base_check_dir_path = check_php_tag_package_path[0:last_index]
    trunk_path = os.path.join(base_check_dir_path, "trunk")
    if not os.path.exists(trunk_path):
        raise MyServiceException("检查: " + svn_tag_package_list_item + " 时发现文件不符合规范")
    if forbid_dir_list:
        forbid_dir_lists = forbid_dir_list.split(";")
        for item in forbid_dir_lists:
            if not item or item == "":
                continue
            forbid_path = os.path.join(trunk_path, item)
            if os.path.exists(forbid_path):
                raise MyServiceException("检查: " + svn_tag_package_list_item + " 时发现文件不符合规范,文件存在禁止的目录(%s)" % forbid_path)
            # 禁止目录中是否包含通配符
            if forbid_path.find("*") > 0:
                if len(glob.glob(forbid_path)) > 0:
                    raise MyServiceException(
                        "检查: " + svn_tag_package_list_item + " 时发现文件不符合规范,文件存在禁止的目录(%s)" % forbid_path)


def check_deploy_php(request_data):
    svn_tag_package = request_data["svn_tag_package"]
    project_type = request_data["project_type"]
    deploy_env = request_data["deploy_env"]
    project = request_data["project"]

    # 查询svn资产信息
    svn_data = json.loads(svn.get_decrypt())[0]["svn"]
    host = svn_data["host"]
    username = svn_data["username"]
    password = svn_data["password"]

    if svn_tag_package.find("\n") > 0:
        svn_tag_package_list = svn_tag_package.splitlines()
    else:
        svn_tag_package_list = [svn_tag_package]
    # 模板数据
    projects = json.loads(template.get())[0]["template"][project_type][deploy_env]["projects"]
    project_template_data = projects[project]
    # 部署信息
    deploy_info = project_template_data["deploy_env"]
    forbid_dir_list = deploy_info["forbid_dir_list"]
    display_content_area = ""
    for svn_tag_package_list_item in svn_tag_package_list:
        if not svn_tag_package_list_item or svn_tag_package_list_item == "":
            continue
        check_php_url_tag_package(svn_tag_package_list_item, host)
        # 检出svn tag package
        svn_tag_package_file_path = MySVN.checkout_file(username, password, svn_tag_package_list_item)
        if not os.path.exists(svn_tag_package_file_path):
            raise MyServiceException("检查: " + svn_tag_package_list_item + " 时发现包不存在")
        # 解压文件
        un_package_path = MyArchive.extra_file(svn_tag_package_file_path)
        # 判断该压缩文件中的文件是否符合规范
        check_php_tag_package_standard(svn_tag_package_list_item, svn_tag_package_file_path, forbid_dir_list)
        # 添加svn树状列表文字到日志
        un_package_path_path_tree = my_path.get_path_tree(un_package_path)
        display_content_area += "取包地址为: %s \n" % svn_tag_package_list_item
        display_content_area += "包中文件为: %s \n" % un_package_path_path_tree
    return display_content_area


def deploy_php(request_data):  # 原始方式直接构建
    try:
        process_id = request_data["process_id"]
        svn_tag_package = request_data["svn_tag_package"]
        project_type = request_data["project_type"]
        deploy_env = request_data["deploy_env"]
        project = request_data["project"]

        project_manage__work_order_process__run_manage_result_log_co.insert_one({
            "process_id": process_id,
            "log": "开始部署",
            "is_exe_success": True,
        })
        # 资产数据
        jenkins_data = json.loads(jenkins.get_decrypt())[0]["jenkins"]
        # 模板数据
        projects = json.loads(template.get())[0]["template"][project_type][deploy_env]["projects"]
        project_template_data = projects[project]

        # 构建信息
        build_info = project_template_data["build_env"]
        build_info_host = build_info["host"]
        build_info_job_name = build_info["job_name"]

        cur_jenkins = jenkins_data[build_info_host]
        cur_jenkins_url = cur_jenkins["url"]
        cur_jenkins_username = cur_jenkins["username"]
        cur_jenkins_password = cur_jenkins["password"]
        my_jenkins = MyJenkins(cur_jenkins_url, cur_jenkins_username, cur_jenkins_password)

        revision, last_build_number = my_jenkins.build_job(build_info_job_name, {"FILELIST": svn_tag_package})
        if not revision or revision == "":
            raise MyServiceException("回滚版本不能为空")
        project_manage__work_order_process__run_manage_process_process_project_rb_co.insert_one({
            "process_id": process_id,
            "svn_tag_package": svn_tag_package,
            "project_type": project_type,
            "deploy_env": deploy_env,
            "project": project,
            "revision": revision,
        })
        project_manage__work_order_process__run_manage_result_log_co.insert_one({
            "process_id": process_id,
            "log": "部署成功",
            "is_exe_success": True,
        })
        project_manage__work_order_process__run_manage_result_log_co.insert_one({
            "process_id": process_id,
            "log": "已经为回滚做好准备,jenkins构建job的id为: %s ,回滚版本为:%s" % (last_build_number, revision),
            "is_exe_success": True,
        })

        run_manage.upgrade_process_service_invoke_status(process_id, True)
    except MyServiceException as e:
        print(e)
        project_manage__work_order_process__run_manage_result_log_co.insert_one({
            "process_id": process_id,
            "log": "部署失败: " + e.msg,
            "is_exe_success": True,
        })
        run_manage.upgrade_process_service_invoke_status(process_id, False)
        raise e


# process_type = "project_deploy"
process_template_arr = ["project_deploy", "project_deploy_with_sql"]


@app.route('/do_project_deploy', methods=['POST'])
def do_project_deploy():
    try:
        request_data = common_service.check_request_dat_not_null(
            ["title", "project_type", "deploy_env", "deploy_target", "project", "process_template_id"])
        title = request_data["title"]
        project_type = request_data["project_type"]
        deploy_env = request_data["deploy_env"]
        process_template_id = request_data["process_template_id"]

        deploy_target = request_data["deploy_target"]
        project = request_data["project"]
        apply_process = request_data["apply_process"]
        display_content = "项目类型为: %s \n 部署环境为: %s \n 部署目标为: %s \n 项目为: %s \n " % (
            project_type, deploy_env, deploy_target, project)

        last_process_template_arr_index = 0
        if request_data.__contains__("code_inner_sql"):
            code_inner_sql = request_data["code_inner_sql"]
        else:
            code_inner_sql = None
        if code_inner_sql and code_inner_sql.strip() != "":
            last_process_template_arr_index = 1
        store_data = {
            "project_type": project_type,
            "deploy_env": deploy_env,
            "deploy_target": deploy_target,
            "project": project,
            "code_inner_sql": code_inner_sql,
        }
        prepare_work_order_list = None
        if "prepare_work_order_list" in request_data:
            prepare_work_order_list = request_data["prepare_work_order_list"]  # 前置工单
            display_content += "前置工单: %s \n " % prepare_work_order_list

        if "java" == project_type:
            common_service.check_request_dat_not_null(
                ["namespace", "image_id"])
            namespace = request_data["namespace"]
            image_id = request_data["image_id"]
            store_data["namespace"] = namespace
            store_data["image_id"] = image_id
            # 部署名称
            deploy_name = json.loads(template.get())[0]["template"][project_type][deploy_env]["projects"][project][
                "deploy_name"]
            store_data["deploy_name"] = deploy_name
            display_content += "命名空间为: %s \n 镜像ID为: %s \n 部署名称为: %s \n  \n\n\n " % (namespace, image_id, deploy_name)
        else:
            common_service.check_request_dat_not_null(
                ["svn_tag_package"])
            svn_tag_package = request_data["svn_tag_package"]
            # display_content += "取包地址为: %s \n \n\n\n " % svn_tag_package
            store_data["svn_tag_package"] = svn_tag_package
            # 检查包是否合理
            display_content_area = check_deploy_php(request_data)
            display_content += display_content_area

        # 流程
        finish_result = {
            "method": "POST",
            "url": "http://localhost:8080/project_manage/deploy_server/apply/finish_project_deploy",
            "rb_url": "http://localhost:8080/project_manage/deploy_server/apply/rollback_project_deploy",
        }
        process_id, next_step = run_manage.process_start(apply_process,
                                                         process_template_arr[last_process_template_arr_index],
                                                         finish_result, title,
                                                         display_content,
                                                         deploy_env, process_template_id,
                                                         prepare_work_order_list,
                                                         system_tag=project_type + ":" + project)
        store_data["process_id"] = process_id
        # 存储内容等待流程完成时去执行
        project_manage__work_order_process__run_manage_process_project_deploy_co.insert_one(store_data)
        project_manage__work_order_process__run_manage_result_log_co.insert_one({
            "process_id": process_id,
            "log": "创建流程",
            "is_exe_success": True,
        })
        run_manage.process_after_trigger(process_id, next_step)
        return {}
    except MyServiceException as e:
        print(e)
        return ResResult.return500(str(e))


@app.route('/finish_project_deploy', methods=['POST'])
def finish_project_deploy():
    try:
        request_data = common_service.check_request_dat_not_null(
            ["process_instance_id"])
        process_instance_id = request_data["process_instance_id"]
        # 查询对应流程id的执行内容
        db_res_data = json.loads(
            dumps(project_manage__work_order_process__run_manage_process_project_deploy_co.find_one(
                filter={'process_id': process_instance_id})))
        project_type = db_res_data["project_type"]
        if "java" == project_type:
            deploy_java(db_res_data)
        else:
            threading.Thread(target=deploy_php, args=[db_res_data]).start()
        return {}
    except MyServiceException as e:
        print(e)
        return ResResult.return500(str(e))


@app.route('/rollback_project_deploy', methods=['POST'])
def rollback_project_deploy():
    try:
        request_data = common_service.check_request_dat_not_null(
            ["process_instance_id"])
        process_instance_id = request_data["process_instance_id"]
        # 查询对应流程id的执行内容
        db_res_data = json.loads(
            dumps(project_manage__work_order_process__run_manage_process_process_project_rb_co.find_one(
                filter={'process_id': process_instance_id})))
        project_type = db_res_data["project_type"]
        deploy_env = db_res_data["deploy_env"]

        if "java" == project_type:
            data_namespace = db_res_data["data_namespace"]
            data_image_id = db_res_data["data_image_id"]
            deploy_name = db_res_data["deploy_name"]
            asset_manage__deploy_server__k8s_co_one = \
                json.loads(common_service.query(asset_manage__deploy_server__k8s_co))[
                    0]
            data_k8s = asset_manage__deploy_server__k8s_co_one["k8s"]
            data_k8s_env = data_k8s[deploy_env]
            data_k8s_host = data_k8s_env["host"]
            data_k8s_token = data_k8s_env["token"]
            my_k8s = MyK8s(data_k8s_host, data_k8s_token)
            project_manage__work_order_process__run_manage_result_log_co.insert_one({
                "process_id": process_instance_id,
                "log": "开始回滚部署<br/>" + data_image_id + "<br/>",
                "is_exe_success": True,
            })
            my_k8s.update_image(data_namespace, deploy_name, data_image_id)
        else:
            project = db_res_data["project"]
            revision = db_res_data["revision"]
            jenkins_data = json.loads(jenkins.get_decrypt())[0]["jenkins"]
            projects = json.loads(template.get())[0]["template"][project_type][deploy_env]["projects"]
            project_template_data = projects[project]
            build_info = project_template_data["build_env"]
            build_info_host = build_info["host"]
            build_info_job_name = build_info["job_name"]
            cur_jenkins = jenkins_data[build_info_host]
            cur_jenkins_url = cur_jenkins["url"]
            cur_jenkins_username = cur_jenkins["username"]
            cur_jenkins_password = cur_jenkins["password"]
            my_jenkins = MyJenkins(cur_jenkins_url, cur_jenkins_username, cur_jenkins_password)
            project_manage__work_order_process__run_manage_result_log_co.insert_one({
                "process_id": process_instance_id,
                "log": "开始回滚部署<br/>" + str(revision) + "<br/>",
                "is_exe_success": True,
            })
            my_jenkins.build_job(build_info_job_name, {"ROLLBACK": revision}, False)

        project_manage__work_order_process__run_manage_result_log_co.insert_one({
            "process_id": process_instance_id,
            "log": "回滚成功",
            "is_exe_success": True,
        })
        return {}
    except MyServiceException as e:
        print(e)
        project_manage__work_order_process__run_manage_result_log_co.insert_one({
            "process_id": process_instance_id,
            "log": "回滚失败,原因:%s" % str(e),
            "is_exe_success": False,
        })
        return ResResult.return500(str(e))


process_v1 = ["dev -> test -> product -> product_team"]


@app.route('/get_process', methods=['GET'])
def get_process():
    return json.dumps(process_v1)
