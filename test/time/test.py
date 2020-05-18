import time


def test_convert_timestamp2str():
    curtime = 1569208475495 / 1000
    time_obj = time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.localtime(curtime))
    print(time_obj)


if __name__ == '__main__':
    test_convert_timestamp2str()
