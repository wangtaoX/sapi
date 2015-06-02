#!/usr/bin/env python
# encoding: utf-8
import sys
import traceback
from sqlalchemy.orm import exc

from oslo.config import cfg
from oslo.db import exception

from torconf import models
from torconf import models_lv
from torconf import rpc
from torconf import topology
from torconf import exceptions

VXLAN = "vxlan"

def import_class_ins(import_str, *args, **kwargs):
    mod_str, _sep, class_str = import_str.rpartition('.')
    __import__(mod_str)
    try:
        return getattr(sys.modules[mod_str], class_str)(*args, **kwargs)
    except AttributeError:
        raise ImportError('Class %s cannot be found (%s)' %
                (class_str,
                    traceback.format_exception(*sys.exc_info())))

class DriverManager(object):
    def __init__(self):
        self._drivers = {}

    def __setitem__(self, type, obj):
        self._drivers[type] = obj

    def __getitem__(self, type):
        return self._drivers[type]

class Sapi():
    def __init__(self):
        self._setup_rpc()
        self._load_switch_drivers()
        self._setup_topology()

    def _load_switch_drivers(self):
        self.switch_drivers = DriverManager()
        for type, class_str in cfg.CONF.switchs.items():
            try:
                self.switch_drivers[type] = import_class_ins(class_str)
            except:
                print "Load _driver %s error" %(class_str)

    def _setup_rpc(self):
        self.rpc = rpc.RpcClient.create('q-plugin')

    def _setup_topology(self):
        self.tors = topology.TopofRacks([tor for tor in models.get_tors()])

    def _get_net_from_body(self, body):
        network = body["network"]
        net = {}

        net["network_id"] = network["id"]
        net["tenant_id"] = network["tenant_id"]
        net["segmentation_type"] = network["provider:network_type"]
        net["segmentation_id"] = network["provider:segmentation_id"]
        net["admin_state_up"] = network["admin_state_up"]
        net["shared"] = network["shared"]
        return net

    def _get_port_from_body(self, body):
        port = body["port"]
        p = {}

        p["port_id"] = port["id"]
        p["tenant_id"] = port["tenant_id"]
        p["network_id"] = port["network_id"]
        p["device_id"] = port["device_id"]
        p["device_owner"] = port["device_owner"]
        p["status"] = port["status"]
        p["admin_state_up"] = port["admin_state_up"]
        p["binding_host_id"] = port["binding:host_id"]
        p["mac_address"] = port["mac_address"]
        fixed_ips = port["fixed_ips"]
        if len(fixed_ips) >= 0:
            p["ip_address"] = fixed_ips[0]["ip_address"]
            p["subnet_id"] = fixed_ips[0]["subnet_id"]
        return p

    def _get_subnet_from_body(self, body):
        subnet = body['subnet']
        s = {}

        s["subnet_id"] = subnet["id"]
        s["tenant_id"] = subnet["tenant_id"]
        s["network_id"] = subnet["network_id"]
        s["shared"] = subnet["shared"]
        s["enable_dhcp"] = subnet["enable_dhcp"]
        return s

    def create_network(self, request, body=None, **kwargs):
        net = self._get_net_from_body(body)
        try:
            models.save_net(net)
        except Exception as e:
            raise exceptions.SapiBadRequest(str(e))

    def show_network(self, request, id, **kwargs):
        try:
            return models.get_net(id)
        except exc.NoResultFound:
            raise exceptions.SapiNotFound(message=("network %s could not be found" %(id)))

    def update_network(self, request, id, body=None, **kwargs):
        net = self._get_net_from_body(body)
        try:
            models.update_net(id, net)
        except exc.NoResultFound:
            raise exceptions.SapiNotFound(message=("network %s could not be found" %(id)))
        except Exception as e:
            raise exceptions.SapiBadRequest(str(e))

    def delete_network(self, request, id, **kwargs):
        try:
            models.delete_net(id)
        except exc.NoResultFound:
            raise exceptions.SapiNotFound(message=("network %s could not be found" %(id)))

    def create_port(self, request, body=None, **kwargs):
        port = self._get_port_from_body(body)
        try:
            models.save_port(port)
        except Exception as e:
            raise exceptions.SapiBadRequest(str(e))

    def delete_port(self, request, id, **kwargs):
        try:
            models.delete_port(id)
        except exc.NoResultFound:
            raise exceptions.SapiNotFound(message=("port %s could not be found" %(id)))

    def show_port(self, request, id, **kwargs):
        try:
            return models.get_port(id)
        except exc.NoResultFound:
            raise exceptions.SapiNotFound(message=("port %s could not be found" %(id)))

    def update_port(self, request, id, body=None, **kwargs):
        port = self._get_port_from_body(body)
        port["id"] = id
        try:
            models.update_port(id, port)
        except exc.NoResultFound:
            raise exceptions.SapiNotFound(message=("port %s could not be found" %(id)))
        except Exception as e:
            raise exceptions.SapiBadRequest(str(e))

    def create_subnet(self, request, body=None, **kwargs):
        subnet = self._get_subnet_from_body(body)
        try:
            models.save_subnet(subnet)
        except Exception as e:
            raise exceptions.SapiBadRequest(str(e))

    def delete_subnet(self, request, id, **kwargs):
        try:
            models.delete_subnet(id)
        except exc.NoResultFound:
            raise exceptions.SapiNotFound(message=("port %s could not be found" %(id)))

    def show_subnet(self, request, id, **kwargs):
        try:
            return models.get_subnet(id)
        except exc.NoResultFound:
            raise exceptions.SapiNotFound(message=("port %s could not be found" %(id)))

    def update_subnet(self, request, id, body=None, **kwargs):
        subnet = self._get_subnet_from_body(body)
        subnet["id"] = id
        try:
            models.update_subnet(id, subnet)
        except exc.NoResultFound:
            raise exceptions.SapiNotFound(message=("port %s could not be found" %(id)))
        except Exception as e:
            raise exceptions.SapiBadRequest(str(e))

    def create_sync(self, request, body=None, **kwargs):
        try:
            models.clear_nets()
            models.clear_ports()
            models.clear_subnets()
            data = body["sina_openstack"]

            for net in data["network"]:
                n = self._get_net_from_body({"network":net})
                models.save_net(n)
            for port in data["port"]:
                p = self._get_port_from_body({"port":port})
                models.save_port(p)
            for subnet in data["subnet"]:
                s = self._get_subnet_from_body({"subnet":subnet})
                models.save_subnet(s)

        except Exception as e:
            raise exceptions.SapiBadRequest(str(e))

    def create_localvlan(self, request, body=None, **kwargs):
        network_id, host, port_id = body["netid"], body["host"], body["portid"]

        tor_ip = self.tors.get_up_tor(host)
        if not tor_ip:
            raise exceptions.SapiNotFound(message=("host %s could not be found" %(host)))

        try:
            net = models.get_net(network_id)
            port = models.get_port(port_id)
            vlan, index, new = self.tors.get_localvlan(net, port, tor_ip, host)
            if vlan < 0:
                raise exceptions.SapiNoAvaVlanError("vlan id out of range.")

            if not models_lv.is_exists_port_vlan_mapping(tor_ip, vlan, index):
                tor = models.get_tor(tor_ip)
                tunnels = [t["tunnel_id"] for t in models_lv.get_tunnnels()]
                if not self.switch_drivers[tor["type"]].initialize(tor_ip, "sinanp", "sinanp"):
                    raise exceptions.SapiTorConfigError("tor %s config error" %(tor_ip))
                if not self.switch_drivers[tor["type"]].newvlan2vxlan(index, vlan, net["segmentation_id"]):
                    raise exceptions.SapiTorConfigError("tor %s config error" %(tor_ip))
                if not self.switch_drivers[tor["type"]].ensureVxlanWithTunnel([net["segmentation_id"]], tunnels):
                    raise exceptions.SapiTorConfigError("tor %s config error" %(tor_ip))
            if new:
                models_lv.save_vlan_allocations({"network_id":network_id,
                                                 "tor_ip":tor_ip,
                                                 "vlan_id":vlan,
                                                 "allocated":True,
                                                 "shared":net["shared"]})
                models_lv.save_vsi({"tor_ip":tor_ip, "vxlan":net["segmentation_id"]})
            models_lv.save_port_vlan_mapping({"port_id":port_id,
                                              "network_id":network_id,
                                              "tor_ip":tor_ip,
                                              "vlan_id":vlan,
                                              "index":index})
        except exc.NoResultFound:
            raise exceptions.SapiNotFound(message=("resourse could not be found"))
        except exception.DBDuplicateEntry:
            raise exceptions.SapiBadRequest("db duplicateEntry error")

    def delete_localvlan(self, request, id, body=None, **kwargs):
        port_id = id
        only_index = True
        try:
            pvm = models_lv.get_port_vlan_mapping(port_id)
            network_id, tor_ip = pvm["network_id"], pvm["tor_ip"]
            net = models.get_net(network_id)
            tor = models.get_tor(tor_ip)
            tor_ip, type = tor["tor_ip"], tor["type"]
            vlan = pvm["vlan_id"]
            count = models_lv.get_pvm_count_by_net(tor_ip, network_id)
            icount = models_lv.get_pvm_count_by_tor_index(tor_ip, pvm["index"])

            if count == 1:
                self.tors.delete_localvlan(network_id, tor_ip, vlan, net["shared"])
                only_index = False
                models_lv.delete_vsi(tor_ip, net["segmentation_id"])
                models_lv.delete_vlan_allocations(tor_ip, network_id)

            if icount <= 1:
                if not self.switch_drivers[type].initialize(tor_ip, "sinanp", "sinanp"):
                    raise exceptions.SapiTorConfigError("tor %s config error" %(tor_ip))
                if not self.switch_drivers[type].deletevlan2vxlan(
                        pvm["index"], vlan,
                        net["segmentation_id"],
                        only_index=only_index):
                    raise exceptions.SapiTorConfigError("tor %s config error" %(tor_ip))

            models_lv.delete_port_vlan_mapping(port_id)
        except exc.NoResultFound:
            raise exceptions.SapiNotFound(message=("port %s could not be found" %(port_id)))

    def delete_tor(self, request, id, body=None, **kwargs):
        try:
            tor = models.get_tor(id)
            src, mgr, type = tor["tunnel_src_ip"], tor["tor_ip"], tor["type"]

            t1, t2 = models_lv.get_tunnel_with_tor(mgr, src)
            for tunnel in t1:
                id = tunnel["tunnel_id"]
                if not self.switch_drivers[type].initialize(mgr, "sinanp", "sinanp"):
                    raise exceptions.SapiTorConfigError("tor %s config error" %(mgr))
                if not self.switch_drivers[type].deletetunnel(id):
                    raise exceptions.SapiTorConfigError("tor %s config error" %(mgr))
                models_lv.delete_tunnel(mgr, id)
            models.delete_tor(mgr)

            for tunnel in t2:
                mgr, id = tunnel["tor_ip"], tunnel["tunnel_id"]
                type = models.get_tor(mgr)["type"]
                if not self.switch_drivers[type].initialize(mgr, "sinanp", "sinanp"):
                    raise exceptions.SapiTorConfigError("tor %s config error" %(mgr))
                if not self.switch_drivers[type].deletetunnel(id):
                    raise exceptions.SapiTorConfigError("tor %s config error" %(mgr))
                models_lv.delete_tunnel(mgr, id)

        except exc.NoResultFound:
            raise exceptions.SapiNotFound(message=("tor %s could not be found" %(id)))

    def create_tor(self, request, body=None, **kwargs):
        type, src, mgr = body["switch_type"], body["tunnel_src"], body["mgr"]
        existinging_tors = models.get_tors()
        existing_tunnel_ips = self.rpc.tunnel_sync(src, VXLAN)
        tunnel_ids = []

        #initialize the connection to the switch.
        #TODO: make the initialization work inside the driver context.
        if not self.switch_drivers[type].initialize(mgr, "sinanp", "sinanp"):
            raise exceptions.SapiTorConfigError("tor %s config error" %(mgr))

        #select all vsis(vxlan) already existed on switch.
        vsis = [v["vxlan"] for v in models_lv.get_vsis_by_tor(mgr)]
        for tunnel in existing_tunnel_ips["tunnels"]:
            tunnel_ip = tunnel["ip_address"]
            if tunnel_ip == src:
                continue
            #make a new tunnel.
            status, tunnel_id = self.switch_drivers[type].newtunnel(src, tunnel_ip)
            if not status:
                raise exceptions.SapiTorConfigError("tor %s config error" %(mgr))
            tunnel_ids.append(tunnel_id)
            models_lv.save_tunnel({"tor_ip":mgr,
                                   "tunnel_id":tunnel_id,
                                   "dst_addr":tunnel_ip})

        #ensure all vsis associated with each new tunnels
        if not self.switch_drivers[type].ensureVxlanWithTunnel(vsis, tunnel_ids):
            raise exceptions.SapiTorConfigError("tor %s config error" %(mgr))
        models.save_tor({"type":type, "tunnel_src_ip":src, "tor_ip":mgr})

        #make a full coverage tunnel sync, we should also configure the existing switch.
        for _, tor in existinging_tors.items():
            mgr = tor["tor_ip"]
            vsis = [v["vxlan"] for v in models_lv.get_vsis_by_tor(mgr)]
            type = models.get_tor(mgr)["type"]

            #initialize the driver context and make a new tunnel.
            if not self.switch_drivers[tor["type"]].initialize(mgr, "sinanp", "sinanp"):
                raise exceptions.SapiTorConfigError("tor %s config error" %(mgr))
            status, tunnel_id = self.switch_drivers[type].newtunnel(tor["tunnel_src_ip"], src)
            if not status:
                raise exceptions.SapiTorConfigError("tor %s config error" %(mgr))

            #ensure new tunnel associated with existed vsis
            if not self.switch_drivers[type].ensureVxlanWithTunnel(vsis, [tunnel_id]):
                raise exceptions.SapiTorConfigError("tor %s config error" %(mgr))
            models_lv.save_tunnel({"tor_ip":mgr,
                                   "tunnel_id":tunnel_id,
                                   "dst_addr":src})

    def index_topology(self, request, **kwargs):
        return {"topology":self.tors.topology,
                "topology_sp":self.tors.topology_sp}

def get_instance():
    return Sapi()
