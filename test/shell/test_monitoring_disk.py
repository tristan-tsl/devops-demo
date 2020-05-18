import os
import time
if __name__ == '__main__':
    while True:
        data = os.system("du -sh ./var/test")
        print data
        time.sleep(1)