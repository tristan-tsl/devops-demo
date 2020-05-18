from component.my_server import MyServer


def prepare_init_command(server_ip, server_username, server_password):
    # wget
    my_server = MyServer(server_ip, server_username, server_password)
    try:
        exe_result, stdin = my_server.exe_command("which wget")
        if exe_result != "/usr/bin/wget\n":  # 当不存在wget命令时
            exe_result, stdin = my_server.exe_command("yum install -y wget")  # 安装wget
    except:
        exe_result, stdin = my_server.exe_command("yum install -y wget")  # 安装wget


class Init(object):
    @staticmethod
    def do_init(server_ip, server_username, server_password):
        prepare_init_command(server_ip, server_username, server_password)
