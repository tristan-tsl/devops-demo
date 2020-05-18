import time

import jenkins


class MyJenkins(object):
    def __init__(self, url, username, password):
        self.server = jenkins.Jenkins(url=url, username=username, password=password)

    def build_job(self, job_name, build_args, is_need_info=True):
        self.server.build_job(job_name, build_args)
        last_build_number = self.server.get_job_info(job_name)['nextBuildNumber']
        if not is_need_info:
            return
        while True:
            try:
                build_info = self.server.get_build_info(job_name, last_build_number)
                revision = build_info["changeSet"]["revisions"][0]["revision"]
                return revision, last_build_number
            except:
                pass
            time.sleep(5)
