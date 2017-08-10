# coding:utf-8


import paramiko
import os
import json
import multiprocessing
import fnmatch

DEFAULT_HOST_LIST = '~/.ansible_hosts'
DEFAULT_MODULE_PATH = '~/.ansible'
DEFAULT_MODULE_NAME = 'ping'
DEFAULT_MODULE_ARGS = ''
DEFAULT_PATTERN = '*'


def _executor_hook(x):
	(runner, host) = x
	return runner._executor(host)


class Runner(object):
	def __init__(self, module_path=DEFAULT_MODULE_PATH,
				 module_name=DEFAULT_MODULE_NAME, module_args='',
				 host_list=DEFAULT_HOST_LIST,
				 pattern=DEFAULT_PATTERN,):

		self.module_path = module_path
		self.module_name = module_name
		# self.forks = forks
		self.pattern = pattern
		self.module_args = module_args
		# self.timeout = timeout
		self.host_list = self._parse_hosts(host_list)


	def _parse_hosts(self, host_list):
		''' parse the host inventory file if not sent as an array '''
		if type(host_list) != list:
			host_list = os.path.expanduser(host_list)
			return file(host_list).read().split("\n")
		return host_list
	
	def _matches(self, host_name):
		''' returns if a hostname is matched by the pattern '''
		if host_name == '':
			return False
		if fnmatch.fnmatch(host_name, self.pattern):
			return True
		return False
	
	
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
		
		if self.module_name != "copy":
			outpath = self._copy_module(conn)
			self._exec_command(conn, "chmod +x %s" % outpath)
			cmd = self._command(outpath)
			result = self._exec_command(conn, cmd)
			conn.close()
			return json.loads(result)

	
	def _command(self, outpath):
		cmd = "%s %s" % (outpath, " ".join(self.module_args))
		return cmd
	
	
	def _exec_command(self, conn, cmd):
		stdin, stdout, stdderr = conn.exec_command(cmd)
		result = stdout.read()
		return result


	def _copy_module(self, conn):
		in_path = os.path.expanduser(
			os.path.join(self.module_path, self.module_name)
		)
		
		out_path = os.path.join(
			"/var/spool/",
			"ansible_learn_%s" % self.module_name
		)
		
		sftp = conn.open_sftp()
		sftp.put(in_path, out_path)
		sftp.close()
		return out_path
	
	
	def run(self):
		hosts = [ x for x in self.host_list if self._matches(x)]
		print hosts
		pool = multiprocessing.Pool(3)
		hosts = [ (self, x) for x in hosts ]
		# print hosts
		results = pool.map(_executor_hook, hosts)
		return results
	
	
if __name__ == '__main__':
	r = Runner(
		host_list= DEFAULT_HOST_LIST,
		module_name = 'ping',
		module_args = '',
	)
	
	print r.run()
	# print result.host_list, result.module_path, result.module_name, result.module_args
	