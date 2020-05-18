const deepEqual = function (x, y) {
    // 指向同一内存时
    if (x === y) {
        return true;
    } else if ((typeof x == "object" && x != null) && (typeof y == "object" && y != null)) {
        if (Object.keys(x).length != Object.keys(y).length)
            return false;

        for (var prop in x) {
            if (y.hasOwnProperty(prop)) {
                if (!deepEqual(x[prop], y[prop]))
                    return false;
            } else return false;
        }

        return true;
    } else return false;
};

let my_cookie = {
    set: function (key, val, time) {//设置cookie方法
        let date = new Date(); //获取当前时间
        let expiresDays = time;  //将date设置为n天以后的时间
        date.setTime(date.getTime() + expiresDays * 24 * 3600 * 1000); //格式化为cookie识别的时间
        document.cookie = key + "=" + val + ";expires=" + date.toGMTString();  //设置cookie
    },
    get: function (key) {//获取cookie方法
        /*获取cookie参数*/
        let cookies = document.cookie.replace(/[ ]/g, "");  //获取cookie，并且将获得的cookie格式化，去掉空格字符
        let arrCookie = cookies.split(";");  //将获得的cookie以"分号"为标识 将cookie保存到arrCookie的数组中
        let tips;  //声明变量tips
        for (var i = 0; i < arrCookie.length; i++) {   //使用for循环查找cookie中的tips变量
            var arr = arrCookie[i].split("=");   //将单条cookie用"等号"为标识，将单条cookie保存为arr数组
            if (key == arr[0]) {    //匹配变量名称，其中arr[0]是指的cookie名称，如果该条变量为tips则执行判断语句中的赋值操作
                tips = arr[1];    //将cookie的值赋给变量tips
                break;          //终止for循环遍历
            }
        }
        return tips;
    },
    del: function (key) { //删除cookie方法
        let date = new Date(); //获取当前时间
        date.setTime(date.getTime() - 10000); //将date设置为过去的时间
        document.cookie = key + "=v; expires =" + date.toGMTString();//设置cookie
    }
};


// 参考文档: https://g.alicdn.com/dingding/opendoc/docs/_identityverify/tab5.html?t=1467363847933
// 关键词： 钉钉扫码登录集成
let is_dev_local_env = false;
// is_dev_local_env = true;
let url_prefix = "http://" + window.location.host;
if (is_dev_local_env) {
    url_prefix = "http://yibainetwork1.natapp1.cc";
}
const dingding_login_code_str = "dingding_login_code";
const dingding_login_name_str = "dingding_login_name";
const dingding_login_openid_str = "dingding_login_openid";


const do_auth = function () {
    component.$Modal.error({
        title: "未认证,请扫码登录",
        width: 500,
        content: '<div id="login_container"></div>',
    });
    const dingding_scan_login = async function () {
        if (!document.getElementById("login_container")) {
            return setTimeout(dingding_scan_login, 1000);
        }
        const appId_data = await axios.get(url_prefix + "/login/appId");
        var appid = appId_data["data"];
        var url = url_prefix + "/login/dingding_scan";
        var goto = encodeURIComponent('https://oapi.dingtalk.com/connect/oauth2/sns_authorize?appid=' + appid + '&response_type=code&scope=snsapi_login&state=STATE&redirect_uri=' + url);
        DDLogin({
            id: "login_container",
            goto: goto,
            style: "border:none;background-color:#FFFFFF;",
            width: "365",
            height: "400"
        });

        var hanndleMessage = function (event) {
            var origin = event.origin;
            if (origin == "https://login.dingtalk.com") {
                let loginTmpCode = event.data;
                console.log("loginTmpCode", loginTmpCode);
                if (loginTmpCode) {
                    let uri = "?appid=" + appid + "&response_type=code&scope=snsapi_login&state=STATE&redirect_uri=" + url + "&loginTmpCode=" + loginTmpCode;
                    // 通过后台代理接口去访问登录
                    (async function () {
                        const res_data = await axios.post(url_prefix + "/login/proxy_net_request", {
                            url: uri,
                            method: "GET"
                        });
                        console.log(res_data);
                        const res_data_data = res_data.data;
                        const code = res_data_data["code"];
                        const nick = res_data_data["nick"];
                        const openid = res_data_data["openid"];


                        my_cookie.del(dingding_login_code_str);
                        my_cookie.del(dingding_login_name_str);
                        my_cookie.del(dingding_login_openid_str);


                        my_cookie.set(dingding_login_code_str, code, 1);
                        my_cookie.set(dingding_login_name_str, nick, 1);
                        my_cookie.set(dingding_login_openid_str, openid, 1);
                        component.$Modal.success({
                            title: "登录成功",
                            content: "欢迎回来: " + nick
                        });
                        window.parent.location.reload();
                    })();
                }
            }
        };
        if (typeof window.addEventListener != 'undefined') {
            window.addEventListener('message', hanndleMessage, false);
        } else if (typeof window.attachEvent != 'undefined') {
            window.attachEvent('onmessage', hanndleMessage);
        }
    };
    dingding_scan_login();
};


if (window.top != window.self && parent) {
    parent.component.$Loading.finish();
}

let last_auth_fail_timestamp = null;

function init_axios() {
    if (axios) {
        axios.defaults.withCredentials = true;
        axios.defaults.crossDomain = true;
        axios.defaults.headers['Access-Control-Allow-Origin'] = '*';
        axios.defaults.headers.common['token'] = my_cookie.get(dingding_login_code_str);
        axios.interceptors.response.use(function (response) {
            return response;
        }, function (error) {
            const cur_timestamp = new Date().valueOf();
            if (last_auth_fail_timestamp && cur_timestamp - last_auth_fail_timestamp < 1000 * 5) {
                return;
            }
            const response = error["response"];
            if (!response) return;
            const status = response["status"];
            if (401 == status) {
                component.$Message.error({
                    content: error.response.data,
                    duration: 5
                });
                last_auth_fail_timestamp = cur_timestamp;
            }
            return Promise.reject(error);
        });

    }
}

init_axios();
// window.onload = function () {
//     do_auth();
// };
String.prototype.replaceAll = function (FindText, RepText) {
    return this.replace(eval("/" + FindText + "/g"), RepText);
};

function convert_openid_to_nick(users, process_code) {
    if (!process_code) return "";
    let cur_review_process = "";
    let process_list = process_code.split(">");
    for (let i = 0; i < process_list.length; i++) {
        let process_user = process_list[i];
        process_user = process_user.trim();
        if (!process_user || process_user == "") break;
        process_user = process_user.trim();
        const users_one = users[process_user];
        cur_review_process += users_one;
        if (i != process_list.length - 1) {
            cur_review_process += " > ";
        }
    }
    if (!cur_review_process) cur_review_process = "";
    return cur_review_process;
}

const process_status_mapping = {
    "RUNNING": "运行中",
    "FINISH": "已完结",
    "REJECT": "已驳回",
    "DESTROY": "已销毁",
    "DELAY_INVOKE": "延迟执行",
};

function convert_process_status_code_to_name(process_status_code) {
    return process_status_mapping[process_status_code];
}

const process_service_type_mapping = {
    "sql_invoke": "执行SQL",
    "project_deploy": "项目部署",
    "schedule_manage": "调度管理",
};

function convert_process_service_type_to_name(process_service_type) {
    return process_service_type_mapping[process_service_type];
}

const service_invoke_status_mapping = {
    "SUCCESS": "执行成功",
    "INVOKING": "执行中",
    "FAILURE": "执行失败",
};

function convert_service_invoke_status_to_name(service_invoke_status) {
    return service_invoke_status_mapping[service_invoke_status];
}


function jump_url(url) {
    location.href = url;
}