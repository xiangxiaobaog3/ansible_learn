# coding:utf-8
##
###

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
        forks=C.DEFAULT_FORKS):


        self.host_list = self._parse_hosts(host_list)
        self.remote_user = remote_user
        self.module_path = module_path
        self.module_name = module_name
        self.pattern = pattern
        self.timeout = timeout
        self.module_args = module_args
        self.forks = forks
        self._tmp_paths = {}


    # 读取hosts文件
    def _parse_hosts(self, host_list):
        ''' parse the host inventory file if not sent as an array '''
        if type(host_list) != list:
            host_list = os.path.expanduser(host_list)
            return file(host_list).read().split("\n")
        return host_list


    def _matches(self, host_name, pattern=None):
        ''' returns if a hostname is matched by the pattern 返回匹配规则的主机名'''
        if host_name == '':
            return False
        subpatterns = pattern.split(";")
        for subpattern in subpatterns:
            if fnmatch.fnmatch(host_name, subpattern):
                return True
        return False


    # 执行ssh秘钥连接
    def _connect(self, host):
        private_key = paramiko.RSAKey.from_private_key_file('/Users/xiangxiaobao/.ssh/id_rsa')
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
        ''' deletes one or more remote files '''
        for filename in files:
            self._exec_command(conn, "rm -f %s" % filename)

    def _transfer_file(self, conn, source, dest):
        ''' transfers a remote file '''
        self.remote_log(conn, 'COPY remote:%s local:%s' % (source, dest))
        sftp = conn.open_sftp()
        sftp.put(source, dest)
        sftp.close()


    def _transfer_moudle(self, conn):
        '''
        transfers a module file to the remote side to execute it,
        but does not execute it yet
        '''
        outpath = self._copy_module(conn)
        self._exec_command(conn, "chmod +x %s" % outpath)
        return outpath


    def _execute_module(self, conn, outpath):
        '''
        runs a module that has already been transferred
        '''
        cmd = self._command(outpath)
        result = self._exec_command(conn, cmd)
        # self._delete_remote_files(conn, [ outpath ])
        return result


    def _execute_normal_module(self, conn, host):
        '''
        transfer & execute a module that is not 'copy' or 'template'
        because those require extra work.
        '''
        module = self._transfer_moudle(conn)
        result = self._execute_module(conn, module)
        return self._return_from_module(conn, host, result)

    def _parse_kv(self, args):
        options = {}
        for x in args:
            if x.find("=") != -1:   # 不是很清楚为什么是 -1
                k, v = x.split("=")
                options[k] = v
        return options


    def _execute_copy(self, conn, host):
        ''' transfer a file + copy module, run copy module, clean up '''
        self.remote_log(conn, 'COPY remote:%s local:%s' % (self.module_args[0], self.module_args[1]))
        source = self.module_args[0]
        dest = self.module_args[1]
        tmp_dest = self._get_tmp_path(conn, dest.split("/")[-1])

        ftp = conn.open_sftp()
        ftp.put(source, tmp_dest)
        ftp.close()

        # install the copy module

        self.module_name = 'copy'
        outpath = self._copy_module(conn)
        self._exec_command(conn, "chmod +x %s" % outpath)

        # run the copy module6

        self.module_args = [ tmp_dest, dest ]
        cmd = self._command(outpath)
        result = self._exec_command(conn, cmd)
        self._delete_remote_files(conn, [outpath, tmp_dest])

        return self._return_from_module(conn, host, result)


    def _execute_template(self, conn, host):
        source = self.module_args[0]
        dest = self.module_args[1]
        metadata = '/var/spool/setup'

        # first copy the source template over
        tempname = os.path.split(source)[-1]
        temppath = self._get_tmp_path(conn, tempname)
        self.remote_log(conn, 'COPY remote:%s local:%s' % (source, temppath))
        ftp = conn.open_sftp()
        ftp.put(source, temppath)
        ftp.close()

        # install the template module
        self.module_name = 'template'
        outpath = self._copy_module(conn)
        self._exec_command(conn, "chmod +x %s" % outpath)

        # run the template module
        self.module_args = [ temppath, dest, metadata ]
        result = self._exec_command(conn, self._command(outpath))
        # clean up
        self._delete_remote_files(conn, [ outpath, temppath ])
        return self._return_from_module(conn, host, result)


    def _executor(self, host):
        '''
        callback executed in parallel for each host.
        returns(hostname, connected_ok, extra)
        where extra is the result of a successful connect
        or a traceback string
        '''
        ok, conn = self._connect(host)
        if not ok:
            return [ host, False, conn ]
        if self.module_name not in [ 'copy', 'templte' ]:
            return self._execute_normal_module(conn, host)
        elif self.module_name == 'copy':
            return self._execute_copy(conn, host)
        elif self.module_name == 'template':
            return self._execute_template(conn, host)
        else:
            raise Exception("???")


    # 输出参数
    def _command(self, outpath):
        cmd = "%s %s" % (outpath, " ".join(self.module_args))
        return cmd


    def remote_log(self, conn, msg):
        stdin, stdout, stdderr = conn.exec_command('/usr/bin/logger -t ansible_learn -p auth.info %r' % msg)


    # 命令输出
    def _exec_command(self, conn, cmd):
        ''' execute a command over SSH '''
        msg = '%s: %s' % (self.module_name, cmd)
        self.remote_log(conn, msg)
        stdin, stdout, stdderr = conn.exec_command(cmd)
        result = "\n".join(stdout.readlines())
        return result


    def _get_tmp_path(self, conn):
        if conn not in self._tmp_paths:
            output = self._exec_command(conn, "mktemp -d /tmp/ansible.XXXXXX")
            self._tmp_paths[conn] = output.split("\n")[0] + '/'

        return self._tmp_paths[conn]


    # copy模块到远端
    def _copy_module(self, conn):
        ''' transfer a moudle over SFTP '''
        in_path = os.path.expanduser(
            os.path.join(self.module_path, self.module_name)
        )

        out_path = self._get_tmp_path(conn) + self.module_name

        sftp = conn.open_sftp()
        sftp.put(in_path, out_path)
        sftp.close()
        return out_path


    def match_hosts(self, pattern=None):
        ''' return all matched hosts 返回所有匹配的IP地址'''
        return [h for h in self.host_list if self._matches(h, pattern)]



    def run(self):
        ''' xfer & run module on all matched hosts
        为了多进程instancemethod 实例化函数，所以要把_executor_hook放在类外面然后调用回来
        '''

        hosts = self.match_hosts()

        # attack pool of hosts in N forks
        hosts = [(self, x) for x in hosts]
        if self.forks > 5:
            pool = multiprocessing.Pool(self.forks)
            results = pool.map(_executor_hook, hosts)
        else:
            results = [_executor_hook(x) for x in hosts]

        # sort hosts by ones we successfully contacted
        # and ones we did not
        results2 = {
            "contacted": {},
            "dark": {}
        }

        for x in results:
            (host, is_ok, result) = x
            if not is_ok:
                results2["dark"][host] = result
            else:
                results2["contacted"][host] = result

        return results2


if __name__ == '__main__':
    r = Runner(
        module_name='ping',
        module_args='',
        pattern='*',
        forks = 3
    )

    print r.run()