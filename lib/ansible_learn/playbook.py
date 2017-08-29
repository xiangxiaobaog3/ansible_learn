# coding:utf-8

import runner
import constants as C
import yaml

class PlayBook(object):
    '''
    运行ansible playbook, 给一个数据结构或者一个YAML文件.
    playbook是可部署的，配置管理或者自动化命令集.
    多个模式不能同时执行，但是任务可以并行执行，根据forks设置的数值
    '''
    def __init__(self,
        playbook    = None,
        host_list   = C.DEFAULT_HOST_LIST,
        module_path = C.DEFAULT_MODULE_PATH,
        forks       = C.DEFAULT_FORKS,
        timeout     = C.DEFAULT_TIMEOUT,
        remote_user = C.DEFAULT_REMOTE_USER,
        ):

        # 调用重用
        self.host_list = host_list
        self.module_path = module_path
        self.forks = forks
        self.remote_user = remote_user
        self.timeout = timeout

        if type(playbook) == str:
            playbook = yaml.load(file(playbook).read())
        self.playbook = playbook


    def _get_task_runner(self,
        pattern=None,
        host_list=None,
        module_name=None,
        module_args=None):

        '''
        返回合适的运行的任务，最好是数据结构
        '''

        if host_list is None:
            host_list = self.host_list

        return runner.Runner(
            pattern=pattern,
            module_name=module_name,
            module_args=module_args,
            host_list=host_list,
            fork=self.forks,
            remote_user=self.remote_user,
            module_path=self.module_path,
            timeout=self.timeout
        )


    def _run_task(self, pattern, task, host_list=None, conditional=False):
        '''

        '''
        if host_list is None:
            host_list = self.host_list

        instructions = task['do']
        (comment, module_details) = instructions
        (module_name, module_args) = module_details

        namestr = "%s/%s" % (pattern, comment)

        if conditional:
            namestr = "subset/%s" % namestr
        print "TASK [%s]" % namestr

        runner = self._get_task_runner(
            pattern=pattern,
            host_list=host_list,
            module_name=module_name,
            module_args=module_args,
        )

        results = runner.run()

        
    def run(self):
        pass