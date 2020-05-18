# 加载config
import config

config.init()

import os

import urllib3
from flask_cors import CORS

urllib3.disable_warnings()
# 初始化服务器
from flask import Flask, redirect, make_response
import logging
from logging.handlers import TimedRotatingFileHandler
import auth

app = Flask(__name__)

app.config['JSON_AS_ASCII'] = False
app.config['SECRET_KEY'] = os.urandom(24)

CORS(app, supports_credentials=True)


@app.route('/<path:path>')
def static_path(path):
    return app.send_static_file(path)


@app.route('/')
def index():
    return redirect("/index.html")


@app.before_request
def global_interceptor():
    try:
        auth.wrap_authentication()
    except auth.CustomAuthException as e:
        custom_res = make_response(e.msg)
        custom_res.status = "401"
        return custom_res


# 初始化目录
if not os.path.exists("temp"):
    os.mkdir("temp")

# 初始化注册
# # 加载业务类
from service import access_control
from service import security_audit
from service import encrypt_tool
from service import login
from service import user_manage

from service.asset_manage.deploy_server import k8s
from service.asset_manage.deploy_server import jenkins
from service.asset_manage.deploy_server import project_composition
from service.asset_manage.code_server import svn
from service.asset_manage import server_manage
from service.asset_manage.db_manage import mysql
from service.asset_manage.db_manage import oracle

from service.project_manage.work_order_process import run_manage
from service.project_manage.work_order_process import process_template

from service.project_manage.deploy_server import template
from service.project_manage.deploy_server import apply

from service.project_manage.schedule import schedule_server_config
from service.project_manage.schedule import schedule_work_order

from service.project_manage.associate_db import sql_work_order

# 资产管理系统
from system.general_asset_manage_system.service import metadata_manage
from system.general_asset_manage_system.service import data_manage
# 监控模块
from service.alarm import config as alarm_config

# 告警模块
from service.monitoring import config as monitoring_config
from service.monitoring import open_monitoring

# # 注册业务类
app.register_blueprint(access_control.app)
app.register_blueprint(security_audit.app)
app.register_blueprint(encrypt_tool.app)
app.register_blueprint(login.app)
app.register_blueprint(user_manage.app)
app.register_blueprint(k8s.app)
app.register_blueprint(jenkins.app)
app.register_blueprint(project_composition.app)
app.register_blueprint(svn.app)
app.register_blueprint(server_manage.app)
app.register_blueprint(mysql.app)
app.register_blueprint(oracle.app)

app.register_blueprint(run_manage.app)
app.register_blueprint(process_template.app)

app.register_blueprint(template.app)
app.register_blueprint(apply.app)

app.register_blueprint(schedule_server_config.app)
app.register_blueprint(schedule_work_order.app)

app.register_blueprint(sql_work_order.app)

# 资产管理系统
app.register_blueprint(metadata_manage.app)
app.register_blueprint(data_manage.app)

# 监控
app.register_blueprint(monitoring_config.app)
app.register_blueprint(open_monitoring.app)

# 警报
app.register_blueprint(alarm_config.app)

# 启动定时器
from timer import dingding
from timer import init_prometheus_component

dingding.start()
init_prometheus_component.start()

# 初始化日志
if not os.path.exists("logs"):
    os.mkdir("logs")
formatter = logging.Formatter(
    "[%(asctime)s][%(filename)s:%(lineno)d][%(levelname)s][%(thread)d] - %(message)s")
handler = TimedRotatingFileHandler(
    "logs/flask.log", when="D", interval=1, backupCount=15,
    encoding="UTF-8", delay=False, utc=True)
app.logger.addHandler(handler)
handler.setFormatter(formatter)

# current_app.logger.warning("Warning msg")
# current_app.logger.error("Error msg!!!")


# 初始化检测模块
from check import check_process

check_process.check()
