import os
import subprocess

from common.common_service import MyServiceException
from config import project_root_path


class MySVN(object):
    @staticmethod
    def checkout_file(username, password, url):
        """
        检出文件
        :param username: 用户名
        :param password: 密码
        :param url: url地址
        :return:
        """
        print("url: ", url)
        command_login = " --username %s --password %s " % (username, password)
        # 得到url的文件路径
        last_spe = url.rfind("/") + 1
        url_dir_path = url[:last_spe]
        filename = url[last_spe:]
        dir_path = url_dir_path[url_dir_path.find("//") + len("//"):]
        dir_path = os.path.join(project_root_path, "temp", dir_path[dir_path.find("/") + len("/"):])

        url_dir_path_co = url_dir_path[0:url_dir_path.rfind("/")]
        url_dir_path_co = url_dir_path_co[0:url_dir_path_co.rfind("/")]
        dir_path_co = dir_path[0:dir_path.rfind("/")]
        dir_path_co = dir_path_co[0:dir_path_co.rfind("/")]
        if not os.path.exists(dir_path_co):
            command_checkout_dir = "svn co --depth=empty %s %s %s" % (
            url_dir_path_co, dir_path_co, command_login)  # 检出文件目录
            print("command_checkout_dir: ", command_checkout_dir)
            try:
                subprocess.run(command_checkout_dir, shell=True, check=True)
            except Exception as e:
                print(e)
                raise MyServiceException("svn检出目录失败")

        file_path = dir_path + filename

        update_file_path = file_path[0:file_path.rfind("/")]
        command_checkout_file = "svn up %s %s" % (update_file_path, command_login)  # 检出指定文件
        print("command_checkout_file: ", command_checkout_file)
        try:
            subprocess.run(command_checkout_file, shell=True, check=True)
        except Exception as e:
            print(e)
            raise MyServiceException("svn检出文件失败")

        return file_path


"""

        # if os.path.exists(dir_path):
        #     command_cleanup_dir = "svn cleanup %s %s" % (dir_path, command_login)  # 清理文件目录
        #     print("command_cleanup_dir: ", command_cleanup_dir)
        #     try:
        #         subprocess.run(command_cleanup_dir, shell=True, check=True)
        #     except Exception as e:
        #         print(e)
        #         raise MyServiceException("svn清理目录失败")
        
        
        # 删除目录
        # if os.path.exists(file_path[0:file_path.rfind(".")]):
        #     shutil.rmtree(path=file_path[0:file_path.rfind(".")])
        
"""
