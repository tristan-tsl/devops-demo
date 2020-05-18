import os



compress_file_name = "Desktop.rar"
compress_file_name = "C:\\Users\\tristan\\Downloads\\test\\vue.js-practice-master.zip"

import patoolib
def extra_file(file_path):
    file_extra_dir = file_path[0:file_path.rfind(os.path.sep)]
    print("file_extra_dir: ", file_extra_dir)
    if not os.path.exists(file_extra_dir):
        os.mkdir(file_extra_dir)
    patoolib.extract_archive(file_path, outdir=file_extra_dir)
    return file_extra_dir


if __name__ == '__main__':
    print(extra_file(compress_file_name))
    pass
