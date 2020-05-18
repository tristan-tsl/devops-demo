import requests

if __name__ == '__main__':
    url = "https://oapi.dingtalk.com/connect/oauth2/sns_authorize?appid=dingoa6revfp6fjyx6rqmt&response_type=code&scope=snsapi_login&state=STATE&redirect_uri=http://yibainetwork.natapp1.cc/login/dingding_scan&loginTmpCode=92adf79e904f30bb80a1b898e7fb548c"
    res_result = requests.get(url)
    print(res_result.json())