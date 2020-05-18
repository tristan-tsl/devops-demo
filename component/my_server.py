import paramiko

from common import common_service


class MyServer(object):
    def __init__(self, host, username, password, port=22):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(self.host, self.port, self.username, self.password)
        self.client = client

    def __del__(self):
        self.client.close()

    def get_file_content(self, filepath):
        result = []
        sftp_client = self.client.open_sftp()
        remote_file = sftp_client.open(filepath)
        try:
            for line in remote_file:
                result.append(line.replace("\r", ""))
        finally:
            remote_file.close()
            return result

    def upload_local_file(self, local_filepath, remote_filepath):
        t = paramiko.Transport((self.host, self.port))
        t.connect(username=self.username, password=self.password)
        sftp = paramiko.SFTPClient.from_transport(t)
        sftp.put(local_filepath, remote_filepath)
        sftp.close()
        t.close()

    def exe_command(self, command):
        print(">" * 200)
        print("开始执行: ", "exe_command: ", command)
        stdin, stdout, stderr = self.client.exec_command(command)
        exe_result = "\n".join(stdout.readlines())
        exe_err_result = stderr.readlines()
        print("执行结果: ", "exe_command: ", command, "exe_result: ", exe_result, "exe_err_result: ", exe_err_result)
        print("<" * 200)

        if 0 != stdout.channel.recv_exit_status():
            raise common_service.MyServiceException("执行远程命令(%s)失败" % command)
        return exe_result, stdin

    def backup_file(self, from_file_path, to_file_path):
        self.exe_command("/bin/cp -f %s %s" % (from_file_path, to_file_path))

    def move_file(self, from_file_path, to_file_path):
        self.exe_command("mv -f %s %s" % (from_file_path, to_file_path))

    def is_exists_path(self, path):
        sftp = self.client.open_sftp()
        try:
            sftp.stat(path)
            return True
        except IOError:
            return False

    def create_dir(self, dir_path):
        self.exe_command("mkdir -p %s" % dir_path)

    def chmod_777_dir(self, dir_path):
        self.exe_command("chmod 777 %s" % dir_path)
