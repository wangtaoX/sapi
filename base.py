#/usr/bin/env python
# encoding: utf-8

class ConfigFailError(Exception):
    pass

class RequestDataError(Exception):
    pass

class NotAllowMethod(Exception):
    pass

class SwitchDriverBase(object):
    def initialize(self, mgr, user, passwd):
        pass

    def newtunnel(self, src, dst):
        pass

    def deletetunnel(self, tunnel_id):
        pass

    def newvlan2vxlan(self, ifindex, vlan, vxlan):
        pass

    def deletevlan2vxlan(self, ifindex, vlan, vxlan, only_index=False):
        pass

    def ensureVxlanWithTunnel(self, vxlan, tunnel_id):
        pass
