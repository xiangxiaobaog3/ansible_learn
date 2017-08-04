# coding:utf-8

from optparse import OptionParser
import os
import paramiko

DEFAULT_HOST_LIST = '~/.ansible_hosts'
DEFAULT_MODULE_PATH = '~/.ansible'
DEFAULT_MODULE_NAME = 'df'
DEFAULT_MODULE_ARGS = ''


class Cli(object):
	def runner(self):
		parser = OptionParser()
		parser.add_option("-H", "--host-list", dest="host_list",
			help="path to hosts list", default=DEFAULT_HOST_LIST)
		parser.add_option("-L", "--library", dest="module_path",
			help="path to module library", default=DEFAULT_MODULE_PATH)
		parser.add_option("-n", "--name", dest="module_name",
			help="module name to execute", default=DEFAULT_MODULE_NAME)
		parser.add_option("-a", "--args", dest="module_args",
			help="module arguments", default=DEFAULT_MODULE_ARGS)
		
		options, args = parser.parse_args()
		host_list = self._host_list(options.host_list)
		# print host_list


		return Runner(
			module_name=options.module_name,
			module_path=options.module_path,
			module_args=options.module_args,
			host_list=host_list,
		)


	def _host_list(self, host_list):
		host_list = os.path.expanduser(host_list)
		return file(host_list).read().split("\n")



class Runner(object):
	def __init__(self, host_list=[], module_path=None,
				 module_name=None, module_args=''):
		self.host_list = host_list
		self.module_path = module_path
		self.module_name = module_name
		# self.forks = forks
		# self.pattern = pattern
		self.module_args = module_args
		# self.timeout = timeout

	
	def _connect(self, host):
		ssh = paramiko.SSHClient()
		ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		ssh.connect('118.89.234.40', 22, 'root', 'bao982@')
		return ssh


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
		host = [ h for h in self.host_list ]
		print host
		return self._executor(host)
	
if __name__ == '__main__':
	r = Runner(
		host_list=['118.89.234.40'],
		module_path='~/.ansible',
		module_name='df',
		module_args='',
	)
	print r.run()
	# print result.host_list, result.module_path, result.module_name, result.module_args
	