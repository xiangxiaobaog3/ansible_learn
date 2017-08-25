# coding:utf-8

import runner
import constants as C
import yaml

class PlayBook(object):

    def __init__(self,
        playbook    = None,
        host_list   = C.DEFAULT_HOST_LIST,
        module_path = C.DEFAULT_MODULE_PATH,
        forks       = C.DEFAULT_FORKS,
        timeout     = C.DEFAULT_TIMEOUT,
        remote_user = C.DEFAULT_REMOTE_USER,
        ):


        self.runner = runner.Runner(
            host_list=host_list,
            module_path=module_path,
            fork=forks,
            timeout=timeout,
            remote_user=remote_user,
        )

        if type(playbook) == str:
            playbook = yaml.load(file(playbook).read())


    def run(self):
        pass