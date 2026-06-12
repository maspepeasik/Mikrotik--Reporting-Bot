from pysnmp.hlapi import SnmpEngine, CommunityData, UdpTransportTarget, ContextData, ObjectType, ObjectIdentity, getCmd
iterator = getCmd(
    SnmpEngine(),
    CommunityData('public'),
    UdpTransportTarget(('127.0.0.1', 161), timeout=1, retries=0),
    ContextData(),
    ObjectType(ObjectIdentity('1.3.6.1.2.1.1.1.0'))
)
errorIndication, errorStatus, errorIndex, varBinds = next(iterator)
print("Result:", errorIndication, varBinds)
