# coding:utf-8

import lib.ansible_learn.constants as C


class Host(object):

    def __init__(self, name=None, port=None):
        self.name = name
        self.vars = {}
        self.groups = []
        if port and port != C.DEFAULT_REMOTE_PORT:
            self.set_variable('ansible_ssh_port', int(port))

        if self.name is None:
            raise Exception("host name is required")

    def add_group(self, group):
        self.groups.append(group)

    def set_variable(self, key, value):
        self.vars[key] = value