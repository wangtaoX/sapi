import time
import lxml.etree as etree
from ncclient import manager

from torconf.base import SwitchDriverBase

class H3CNetConfDriver(SwitchDriverBase):
    vsi_xml = """
        <config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"
         xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
          <top xmlns="http://www.h3c.com/netconf/config:1.0">
            <L2VPN xc:operation="{operation}">
              <VSIs>
                <VSI>
                  <VsiName>{vsiname}</VsiName>
                </VSI>
              </VSIs>
            </L2VPN>
          </top>
        </config>
    """
    create_vxlan_xml = """
        <config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"
         xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
          <top xmlns="http://www.h3c.com/netconf/config:1.0">
            <VXLAN xc:operation="merge">
              <VXLANs>
                  <Vxlan>
                      <VxlanID>{vxlanid}</VxlanID>
                      <VsiName>{vsiname}</VsiName>
                  </Vxlan>
              </VXLANs>
            </VXLAN>
          </top>
        </config>
    """
    delete_vxlan_xml = """
        <config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"
         xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
          <top xmlns="http://www.h3c.com/netconf/config:1.0">
            <VXLAN xc:operation="remove">
              <VXLANs>
                  <Vxlan>
                      <VxlanID>{vxlanid}</VxlanID>
                  </Vxlan>
              </VXLANs>
            </VXLAN>
          </top>
        </config>
    """
    edit_vxlan_xml = """
        <config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"
         xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
          <top xmlns="http://www.h3c.com/netconf/config:1.0">
            <VXLAN xc:operation="merge">
              <Tunnels>
                  <Tunnel>
                      <VxlanID>{vxlanid}</VxlanID>
                      <TunnelID>{tunnelid}</TunnelID>
                  </Tunnel>
              </Tunnels>
            </VXLAN>
          </top>
        </config>
    """
    create_tunnel_xml = """
        <config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"
         xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
          <top xmlns="http://www.h3c.com/netconf/config:1.0">
            <TUNNEL xc:operation="merge">
              <Tunnels>
                  <Tunnel>
                      <ID>{tunnel_id}</ID>
                      <Mode>24</Mode>
                      <IPv4Addr>
                          <SrcAddr>{src_addr}</SrcAddr>
                          <DstAddr>{dst_addr}</DstAddr>
                      </IPv4Addr>
                  </Tunnel>
              </Tunnels>
            </TUNNEL>
          </top>
        </config>
    """
    delete_tunnel_xml = """
        <config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"
         xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
          <top xmlns="http://www.h3c.com/netconf/config:1.0">
            <TUNNEL xc:operation="remove">
              <Tunnels>
                  <Tunnel>
                      <ID>{tunnel_id}</ID>
                  </Tunnel>
              </Tunnels>
            </TUNNEL>
          </top>
        </config>
    """
    create_ac_xml = """
    <config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"
     xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
        <top xmlns="http://www.h3c.com/netconf/config:1.0">
            <L2VPN xc:operation="merge">
                <ACs>
                    <AC>
                        <IfIndex>{if_index}</IfIndex>
                        <SrvID>{service_id}</SrvID>
                        <VsiName>{vsi_name}</VsiName>
                    </AC>
                </ACs>
            </L2VPN>
        </top>
    </config>
    """
    delete_ac_xml = """
    <config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"
     xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
        <top xmlns="http://www.h3c.com/netconf/config:1.0">
            <L2VPN xc:operation="remove">
                <ACs>
                    <AC>
                        <IfIndex>{if_index}</IfIndex>
                        <SrvID>{service_id}</SrvID>
                    </AC>
                </ACs>
            </L2VPN>
        </top>
    </config>
    """
    create_service_xml = """
    <config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"
     xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
        <top xmlns="http://www.h3c.com/netconf/config:1.0">
            <L2VPN xc:operation="merge">
                <SRVs>
                    <SRV>
                        <IfIndex>{if_index}</IfIndex>
                        <SrvID>{service_id}</SrvID>
                        <Encap>4</Encap>
                        <SVlanRange>{s_vid}</SVlanRange>
                    </SRV>
                </SRVs>
            </L2VPN>
        </top>
    </config>
    """
    delete_service_xml = """
    <config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"
     xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
        <top xmlns="http://www.h3c.com/netconf/config:1.0">
            <L2VPN xc:operation="remove">
                <SRVs>
                    <SRV>
                        <IfIndex>{if_index}</IfIndex>
                        <SrvID>{service_id}</SrvID>
                    </SRV>
                </SRVs>
            </L2VPN>
        </top>
    </config>
    """
    RETRIEVE_AVAILABLE_TUNNEL_ID = """
        <top xmlns="http://www.h3c.com/netconf/data:1.0">
            <TUNNEL xmlns:web="http://www.h3c.com/netconf/base:1.0">
                    <AvailableTunnelID>
                    </AvailableTunnelID>
            </TUNNEL>
        </top>
    """
    def __init__(self):
        self.conn = {}
        self.mgr = None
        self.user= None
        self.passwd = None
        self.timestamp = time.time()

    def initialize(self, mgr, user, passwd):
        self.mgr, self.user, self.passwd = mgr, user, passwd
        if self.mgr not in self.conn:
            self.conn[mgr] = None
        now = time.time()
        expired = int(now - self.timestamp)
        if not self.conn[self.mgr] or expired > 30:
            try:
                self.conn[self.mgr] = manager.connect_ssh(host = self.mgr,
                                            username = self.user,
                                            password = self.passwd,
                                            hostkey_verify = False,
                                            look_for_keys=False)
                self.timestamp = time.time()
            except Exception as e:
                print str(e)
                return False
        return True

    def _check_resp(self, ret):
        if 'ok' in ret.xml:
            return True
        else:
            return False

    def _operation(self, xml):
        try:
            ret = self.conn[self.mgr].edit_config(target='running', config=xml)
            return self._check_resp(ret)
        except:
            return False

    def  _create_vsi_xml(self, name):
        return self.vsi_xml.format(operation="merge", vsiname=name)

    def _delete_vsi_xml(self, name):
        return self.vsi_xml.format(operation="remove", vsiname=name)

    def _create_vsi(self, name):
        return self._operation(self._create_vsi_xml(name))

    def _delete_vsi(self, name):
        return self._operation(self._delete_vsi_xml(name))

    def _create_vxlan_xml(self, vxlan, name):
        return self.create_vxlan_xml.format(vxlanid=vxlan, vsiname=name)

    def _delete_vxlan_xml(self, vxlan):
        return self.delete_vxlan_xml.format(vxlanid=vxlan)

    def _create_vxlan(self, vxlan, name):
        return self._operation(self._create_vxlan_xml(vxlan, name))

    def _delete_vxlan(self, vxlan):
        return self._operation(self._delete_vxlan_xml(vxlan))

    def _edit_vxlan_xml(self, vxlan, tunnel_id):
        return self.edit_vxlan_xml.format(vxlanid=vxlan, tunnelid=tunnel_id)

    def _edit_vxlan_tunnel(self, vxlan, tunnel_id):
        return self._operation(self._edit_vxlan_xml(vxlan, tunnel_id))

    def _create_tunnel_xml(self, tunnel_id, src, dst):
        return self.create_tunnel_xml.format(tunnel_id=tunnel_id, src_addr=src, dst_addr=dst)

    def _delete_tunnel_xml(self, tunnel_id):
        return self.delete_tunnel_xml.format(tunnel_id=tunnel_id)

    def _create_tunnel(self, tunnel_id, src, dst):
        return self._operation(self._create_tunnel_xml(tunnel_id, src, dst))

    def _delete_tunnel(self, tunnel_id):
        return self._operation(self._delete_tunnel_xml(tunnel_id))

    def _create_port_ac_xml(self, index, service_id, vsiname):
        return self.create_ac_xml.format(if_index=index, service_id=service_id, vsi_name=vsiname)

    def _delete_port_ac_xml(self, index, service_id):
        return self.delete_ac_xml.format(if_index=index, service_id=service_id)

    def _create_port_ac(self, index, service_id, vsiname):
        return self._operation(self._create_port_ac_xml(index, service_id, vsiname))

    def _delete_port_ac(self, index, service_id):
        return self._operation(self._delete_port_ac_xml(index, service_id))

    def _create_service_xml(self, index, service_id, s_vid):
        return self.create_service_xml.format(if_index=index, service_id=service_id, s_vid=s_vid)

    def _delete_service_xml(self, index, service_id):
        return self.delete_service_xml.format(if_index=index, service_id=service_id)

    def _create_service(self, index, service_id, s_vid):
        return self._operation(self._create_service_xml(index, service_id, s_vid))

    def _delete_service(self, index, service_id):
        return self._operation(self._delete_service_xml(index, service_id))

    def _get_avaliable_tunnel_id(self):
        id = -1
        def replace_id(s):
            s1 = s.replace('<ID>', '')
            return s1.replace('</ID>', '')
        try:
            configstr = self.RETRIEVE_AVAILABLE_TUNNEL_ID
            ret = self.conn[self.mgr].get(filter=('subtree', configstr))
            x = etree.fromstring(ret.data_xml)
            lines = etree.tostring(x, pretty_print = True).split('\n')
            _lines = [line.strip() for line in lines]
            for line in _lines:
                if line.startswith('<ID>'):
                    id = replace_id(line)
        except Exception as e:
            print str(e)
        return int(id)

    #get an avaliable tunnel id
    def newtunnel(self, src, dst):
        tunnel_id = self._get_avaliable_tunnel_id()
        if tunnel_id == -1:
            return False, tunnel_id
        return self._create_tunnel(tunnel_id, src, dst), tunnel_id

    def deletetunnel(self, tunnel_id):
        return self._delete_tunnel(tunnel_id)

    def newvlan2vxlan(self, index, vlan, vxlan):
        vsiname = "vsi" + str(vxlan)
        print "newvlan2vxlan: vxlan %s vlan %s index %s tor %s" %(vxlan, vlan, index, self.mgr)
        self._create_vsi(vsiname)
        self._create_vxlan(vxlan, vsiname)
        self._create_service(index, vlan, vlan)
        self._create_port_ac(index, vlan, vsiname)
        return True

    def deletevlan2vxlan(self, index, vlan, vxlan, only_index=False):
        vsiname = "vsi" + str(vxlan)
        self._delete_port_ac(index, vlan)
        self._delete_service(index, vlan)
        if only_index:
            return True
        self._delete_vxlan(vxlan)
        self._delete_vsi(vsiname)
        #return (self._delete_port_ac(index, vlan)
        #        and self._delete_service(index, vlan)
        #        and self._delete_vxlan(vxlan)
        #        and self._delete_vsi(vsiname))
        return True

    def ensureVxlanWithTunnel(self, vxlans, tunnel_ids):
        for vxlan in vxlans:
            for tunnel_id in tunnel_ids:
                self._edit_vxlan_tunnel(vxlan, tunnel_id)
        return True
