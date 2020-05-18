import os
import zipfile

import patoolib

from common.common_service import MyServiceException


class MyArchive(object):
    @staticmethod
    def unzip(filepath, file_name):
        zip_file = zipfile.ZipFile(file_name)
        if not os.path.isdir(filepath):
            os.mkdir(filepath)
        for names in zip_file.namelist():
            zip_file.extract(names, filepath + "/")
        zip_file.close()

    @staticmethod
    def un_archive(filename_path):
        if not filename_path:
            return
        archive_format_index = filename_path.rfind(".") + len(".")
        archive_format = filename_path[archive_format_index:]
        filepath = filename_path[:archive_format_index - 1]

        if "zip" == archive_format:
            MyArchive.unzip(filepath, filename_path)
        else:
            raise MyServiceException("解压压缩文件失败, 不支持的文件类型")
        return filepath

    @staticmethod
    def extra_file(file_path):
        file_extra_dir = file_path[0:file_path.rfind(".")]
        if not os.path.exists(file_extra_dir):
            os.mkdir(file_extra_dir)
        patoolib.extract_archive(file_path, outdir=file_extra_dir)
        return file_extra_dir
