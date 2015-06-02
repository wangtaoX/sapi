#!/usr/bin/env python
# encoding: utf-8
import traceback

from torconf import utils
from torconf import models_lv

VLAN_VPC_MIN = 2
VLAN_VPC_MAX = 4000
VLAN_BASE_MIN = 4002
VLAN_BASE_MAX = 4094
NO_AVA_VLAN_ID = -1

SHARED = 'shared'
UNSHARED = 'unshared'
SNMPWALK = 'snmpwalk'

LLDP_LOCAL_OID = "1.0.8802.1.1.2.1.3"
LLDP_REMOTE_OID = "1.0.8802.1.1.2.1.4"

LLDP_LOCAL_ITEMS = [
    "iso.0.8802.1.1.2.1.3.2.0",
    "iso.0.8802.1.1.2.1.3.3.0",
    "iso.0.8802.1.1.2.1.3.4.0",
    "iso.0.8802.1.1.2.1.3.7.1.3",
    "iso.0.8802.1.1.2.1.3.8.1.5"
]

LLDP_REMOTE_ITEMS = [
    "iso.0.8802.1.1.2.1.4.1.1.5",
    "iso.0.8802.1.1.2.1.4.1.1.8",
    "iso.0.8802.1.1.2.1.4.1.1.9",
    "iso.0.8802.1.1.2.1.4.1.1.10",
    "iso.0.8802.1.1.2.1.4.2.1.3"
]

class TopofRacks(object):
    def __init__(self, topofrack):
        self._topofracks = topofrack
        self._topofracks_lvm = {}
        self._topofracks_lvm_cache = {}
        self._topology = {}
        self._topology_sp = {}

        self._init_data()

    @property
    def topology(self):
        if self._topology == {}:
            self._get_topology()
        return self._topology

    @property
    def topology_sp(self):
        if self._topology_sp == {}:
            self._get_topology()
        return self._topology_sp

    @property
    def topofracks(self):
        return self._topofracks

    @topofracks.setter
    def topofracks(self, topofracks):
        self._topofracks = topofracks
        if self._topofracks != []:
            self._get_topology()

    def get_up_tor(self, host):
        for tor in self._topology_sp:
            if host in self._topology_sp[tor]:
                return tor
        return None

    def _get_index(self, host):
        for _, index_info in self._topology.items():
            for index in index_info:
                if index_info[index]["host"] == host:
                    return int(index)

    def _get_vlan_id(self, tor_ip, shared, id):
        vlan = None
        if shared:
            vlan = self._topofracks_lvm[tor_ip][SHARED].get_unused_bits()
        else:
            vlan = self._topofracks_lvm[tor_ip][UNSHARED].get_unused_bits()
        if vlan:
            self._topofracks_lvm_cache[id] = vlan
        return vlan

    def get_localvlan(self, network, port, tor_ip, host):
        id = self._get_cache_id(tor_ip, network["network_id"], network["shared"])
        index = self._get_index(host)

        if id in self._topofracks_lvm_cache:
            vlan = self._topofracks_lvm_cache[id]
            return vlan, index, False

        vlan = self._get_vlan_id(tor_ip, network["shared"], id)
        if not vlan:
            return NO_AVA_VLAN_ID, '', False
        return vlan, index, True

    def _delete_vlan_id(self, tor_ip, shared, id, vlan):
        if shared:
            vlan = self._topofracks_lvm[tor_ip][SHARED].delete_bits(vlan)
        else:
            vlan = self._topofracks_lvm[tor_ip][UNSHARED].delete_bits(vlan)
        del self._topofracks_lvm_cache[id]

    def delete_localvlan(self, network_id, tor_ip, vlan, shared):
        cache_id = ''
        for id in self._topofracks_lvm_cache:
            if id.startswith(tor_ip+network_id):
                cache_id = id
                break
        self._delete_vlan_id(tor_ip, shared, cache_id, vlan)

    def _init_data(self):

        #init topology first
        self._get_topology()

        #init in memory data from database.
        for topofrack in self._topofracks:
            self._topofracks_lvm[topofrack] = {}
            self._topofracks_lvm[topofrack][SHARED] = utils.LocalVLanBitmap(VLAN_BASE_MIN, VLAN_BASE_MAX)
            self._topofracks_lvm[topofrack][UNSHARED] = utils.LocalVLanBitmap(VLAN_VPC_MIN, VLAN_VPC_MAX)

        vas = models_lv.get_vlan_allocations()
        for va in vas:
            cache_id = self._get_cache_id(va["tor_ip"], va["network_id"], va["shared"])
            self._topofracks_lvm_cache[cache_id] = va["vlan_id"]
            if va[SHARED]:
                self._topofracks_lvm[va["tor_ip"]][SHARED].add_bits(va["vlan_id"])
            else:
                self._topofracks_lvm[va["tor_ip"]][UNSHARED].add_bits(va["vlan_id"])

    def _get_cache_id(self, tor, net, shared):
        if shared:
            return tor+net+"-1"
        else:
            return tor+net+"-0"

    def _snmpwalk_cmd(self, community, ip, oid, version='2c'):
        if not oid.startswith('.'):
            oid = '.' + oid
        return [SNMPWALK, '-v', version, '-c', community, ip, oid]

    def _get_topology(self):
        for topofrack in self.topofracks:

            self._topology[topofrack] = {}
            self._topology_sp[topofrack] = []
            local = self._parse_local_data(topofrack)
            remote = self._parse_remote_data(topofrack)

            for index in remote:
                self._topology[topofrack][index] = {}
                self._topology[topofrack][index]['index_name'] = local['indexs'][index]
                self._topology[topofrack][index]['tor_ip'] = topofrack
                self._topology[topofrack][index]['tor'] = local['sysname']
                self._topology[topofrack][index]['host'] = remote[index]['hostname']
                self._topology[topofrack][index]['desc'] = remote[index]['hostdesc']
                self._topology[topofrack][index]['host_ip'] = remote[index]['ip']
                self._topology[topofrack][index]['mac'] = remote[index]['mac']
                self._topology[topofrack][index]['interface'] = remote[index]['desc']
                self._topology_sp[topofrack].append(remote[index]['hostname'])

    def _is_oid(self, oid):
        for i in LLDP_LOCAL_ITEMS + LLDP_REMOTE_ITEMS:
            if oid.startswith(i):
                return i
        return None

    def _parse_local_data(self, ip):
        local = {}
        local['indexs'] = {}
        local['mgrs'] = {}
        cmd = self._snmpwalk_cmd('public', ip, LLDP_LOCAL_OID)
        try:
            returnvalue = utils.execute(cmd)
            for line in [line for line in returnvalue.split('\n') if line != '']:
                content = line.split(' ')
                oid, result= content[0], ' '.join(content[3:])
                result = result.strip("\"")

                case = self._is_oid(oid)
                if not case:
                    continue

                if case == 'iso.0.8802.1.1.2.1.3.2.0':
                    local['mac'] = result
                elif case == 'iso.0.8802.1.1.2.1.3.3.0':
                    local['sysname'] = result
                elif case == 'iso.0.8802.1.1.2.1.3.4.0':
                    local['desc'] = result
                elif case == 'iso.0.8802.1.1.2.1.3.7.1.3':
                    index = int(oid.split('.')[-1])
                    index_name = result
                    local['indexs'][index] = index_name
                elif case == 'iso.0.8802.1.1.2.1.3.8.1.5':
                    index = int(result)
                    mgr = '.'.join(oid.split('.')[-4:])
                    local['mgrs'][index] = mgr
                else:
                    continue
        except RuntimeError:
            print traceback.format_exc()
        finally:
            return local

    def _parse_remote_data(self, ip):
        remote = {}
        cmd = self._snmpwalk_cmd('public', ip, LLDP_REMOTE_OID)
        try:
            returnvalue = utils.execute(cmd)
            for line in [line for line in returnvalue.split('\n') if line != '']:
                content = line.split(' ')
                oid, result= content[0], ' '.join(content[3:])
                result = result.strip("\"")

                case = self._is_oid(oid)
                if not case:
                    continue

                if case == 'iso.0.8802.1.1.2.1.4.2.1.3':
                    index = int(oid.split('.')[-8])
                    if index not in remote:
                        remote[index] = {}
                else:
                    index = int(oid.split('.')[-2])
                    if index not in remote:
                        remote[index] = {}

                if case == 'iso.0.8802.1.1.2.1.4.1.1.5':
                    remote[index]['mac'] = result
                elif case == 'iso.0.8802.1.1.2.1.4.1.1.8':
                    remote[index]['desc'] = result
                elif case == 'iso.0.8802.1.1.2.1.4.1.1.9':
                    remote[index]['hostname'] = result
                elif case == 'iso.0.8802.1.1.2.1.4.1.1.10':
                    remote[index]['hostdesc'] = result
                elif case == 'iso.0.8802.1.1.2.1.4.2.1.3':
                    ip = '.'.join(oid.split('.')[-4:])
                    remote[index]['ip'] = ip
        except RuntimeError:
            print traceback.format_exc()
        finally:
            return remote
