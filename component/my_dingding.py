import requests
from dingtalkchatbot.chatbot import DingtalkChatbot

from config import app_conf

dingding_base_url = "https://oapi.dingtalk.com/sns"
webhook_base = 'https://oapi.dingtalk.com/robot/send?access_token='

webhook = webhook_base + app_conf["dingding"]["robot_msg"]["project_manage"]["access_token"]
xiaoding = DingtalkChatbot(webhook)


def get_access_token():
    resp = requests.get(
        url=dingding_base_url + "/gettoken",
        params=dict(appid=app_conf["dingding"]["login"]["appid"], appsecret=app_conf["dingding"]["login"]["appsecret"])
    )
    resp = resp.json()
    return resp["access_token"]


def get_persistent_code(code, access_token):
    resp = requests.post(
        url="%s/get_persistent_code?access_token=%s" % (dingding_base_url, access_token),
        json=dict(tmp_auth_code=code),
    )
    return resp.json()


def get_sns_token(openid, persistent_code, access_token):
    resp = requests.post(
        url="%s/get_sns_token?access_token=%s" % (dingding_base_url, access_token),
        json=dict(openid=openid, persistent_code=persistent_code),
    )
    res_data = resp.json()
    return res_data["sns_token"]


def get_user_info(sns_token):
    resp = requests.get(
        url=dingding_base_url + "/getuserinfo",
        params=dict(sns_token=sns_token)
    )
    resp = resp.json()
    return resp


def send_msg(msg, ding_id):
    xiaoding.send_text(
        msg=msg,
        at_dingtalk_ids=[ding_id])


class MyDDRobot(object):
    def __init__(self, webhook_url):
        self.dingding_robot = DingtalkChatbot(webhook_url)

    def send_msg(self, msg, ding_id=None):
        self.dingding_robot.send_text(msg=msg, at_dingtalk_ids=[ding_id])
