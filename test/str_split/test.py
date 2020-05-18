from common.common_service import MyServiceException

test_str = "http://www.baidu.com/test.1"


def check_php_url_tag_package(url, svn_server_host):
    url_prefix = url[0:len(svn_server_host)]
    url_suffix_zip = url[len(url)-len(".zip"):]
    url_suffix_rar = url[len(url)-len(".rar"):]

    if url_prefix != svn_server_host:
        raise MyServiceException("检查: " + url + " 时发现文件地址不为允许的svn服务器地址")
    if url_suffix_zip != ".zip" or url_suffix_rar == ".rar":
        raise MyServiceException("检查: " + url + " 文件后缀不为允许的后缀(.zip/.rar)")


if __name__ == '__main__':
    check_php_url_tag_package(test_str, "http://www.baidu.com/")
