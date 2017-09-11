# coding:utf-8

import paramiko
import os
import json
import multiprocessing
import fnmatch
import traceback
import constants as C


def _executor_hook(x):
    ''' callback used by multiprocessing pool '''
    (runner, host) = x
    return runner._executor(host)


class Runner(object):

    def __init__(self,
        module_path=C.DEFAULT_MODULE_PATH,
        module_name=C.DEFAULT_MODULE_NAME,
        host_list=C.DEFAULT_HOST_LIST,
        pattern=C.DEFAULT_PATTERN,
        remote_user=C.DEFAULT_REMOTE_USER,
        module_args=C.DEFAULT_MODULE_ARGS,
        timeout=C.DEFAULT_TIMEOUT,
        fork=C.DEFAULT_FORKS):


        self.host_list = self._parse_hosts(host_list)
        self.remote_user = remote_user
        self.module_path = module_path
        self.module_name = module_name
        self.pattern = pattern
        self.timeout = timeout
        self.module_args = module_args
        self.fork = fork


    # 读取hosts文件
    def _parse_hosts(self, host_list):
        ''' parse the host inventory file if not sent as an array '''
        if type(host_list) != list:
            host_list = os.path.expanduser(host_list)
            return file(host_list).read().split("\n")
        return host_list


    # 匹配数据函数
    def _matches(self, host_name, pattern=None):
        ''' returns if a hostname is matched by the pattern '''
        if host_name == '':
            return False
        if not pattern:
            pattern = self.pattern
        if fnmatch.fnmatch(host_name, pattern):
            return True
        return False


    # 执行ssh秘钥连接
    def _connect(self, host):
        private_key = paramiko.RSAKey.from_private_key_file('/Users/xiangxiaobao/.ssh/qcloud_rsa')
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh.connect(host, port=22, username=self.remote_user, pkey=private_key)
            return [ True, ssh]
        except:
            return [ False, traceback.format_exc()]


    def _return_from_module(self, conn, host, result):
        conn.close()
        try:
            return [ host, True, json.loads(result) ]
        except:
            return [ host, False, result ]


    def _delete_remote_files(self, conn, files):
        for filename in files:
            self._exec_command(conn, "rm -f %s" % filename)


    def _execute_normal_module(self, conn, host, result):
        ''' transfer a module, set it executable, and run it '''

        outpath = self._copy_module(conn)
        self._exec_command(conn, "chmod +x %s" % outpath)
        cmd = self._command(outpath)
        result = self._exec_command(conn, cmd)
        self._delete_remote_files(conn, outpath)
        return self._return_from_module(conn, host, result)


    def _execute_copy(self, conn, host):

        self.remote_log(conn, 'COPY remote:%s local:%s' % (self.module_args[0], self.module_args[1]))
        source = self.module_args[0]
        dest = self.module_args[1]
        tmp_dest = self._get_tmp_path(conn, dest.split("/")[-1])




    # 执行下面的命令的集合
    def _executor(self, host):
        conn = self._connect(host)
        if not conn:
            return [host, None]

        if self.module_name != "copy":
            outpath = self._copy_module(conn)
            self._exec_command(conn, "chmod +x %s" % outpath)
            cmd = self._command(outpath)
            result = self._exec_command(conn, cmd)
            conn.close()
            return json.loads(result)


    # 输出参数
    def _command(self, outpath):
        cmd = "%s %s" % (outpath, " ".join(self.module_args))
        return cmd


    # 命令输出
    def _exec_command(self, conn, cmd):
        stdin, stdout, stdderr = conn.exec_command(cmd)
        result = stdout.read()
        return result


    def remote_log(self, conn, msg):
        stdin, stdout, stdderr = conn.exec_command('/usr/bin/logger -t ansible_learn -p auth.info %r' % msg)


    def _get_tmp_path(self, conn, file_name):
        output = self._exec_command(conn, "mktemp /tmp/%s.XXXXXX" % file_name)
        return output.split("\n")[0]


    # copy模块到远端
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
        pool = multiprocessing.Pool()
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