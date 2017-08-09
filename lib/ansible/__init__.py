# coding:utf-8


import paramiko

DEFAULT_HOST_LIST = '~/.ansible_hosts'
DEFAULT_MODULE_PATH = '~/.ansible'
DEFAULT_MODULE_NAME = 'df'
DEFAULT_MODULE_ARGS = ''



class Runner(object):
	def __init__(self, module_path=None,
				 module_name=None, module_args='',
				 host_list=[]):
		self.host_list = host_list
		self.module_path = module_path
		self.module_name = module_name
		# self.forks = forks
		# self.pattern = pattern
		self.module_args = module_args
		# self.timeout = timeout

	
	def _connect(self, host):
		private_key = paramiko.RSAKey.from_private_key_file('/Users/xiangxiaobao/.ssh/qcloud_rsa')
		ssh = paramiko.SSHClient()
		ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		try:
			ssh.connect(host, port=22, username='root', pkey=private_key)
			return ssh
		except:
			return None


	def _executor(self, host):
		conn = self._connect(host)
		if not conn:
			return [ host, None ]

		cmd = self.module_name
		result = self._exec_command(conn, cmd)
		return result

	
	def _exec_command(self, conn, cmd):
		stdin, stdout, stdderr = conn.exec_command(cmd)
		result = stdout.read()
		return result
		
	
	def run(self):
		for host in self.host_list:
			return self._executor(host)
	
	
if __name__ == '__main__':
	r = Runner(
		host_list= ['118.89.234.40'],
		module_path = '~/ansible',
		module_name = 'df',
		module_args = '',
	)
	
	print r.run()
	# print result.host_list, result.module_path, result.module_name, result.module_args
	