import collections

AbilityDependency = collections.namedtuple('AbilityDependency', ['package', 'ability'])

classic_dependencies = {
    'mitm': AbilityDependency('base', 'Message Interceptor'),
    'debug': AbilityDependency('base', 'Debug Packets'),
    'sendraw': AbilityDependency('base', 'Send Raw Frames'),
    'capture': AbilityDependency('base', 'Sniff Frames'),
    'netfilter': AbilityDependency('base', 'Netfilter Config'),
    'tcpclnt': AbilityDependency('base', 'TCP Client'),
    'tcpsrv': AbilityDependency('base', 'TCP Server'),
    'tlsclnt': AbilityDependency('base', 'TLS Client'),
    'tlssrv': AbilityDependency('base', 'TLS Server'),
    'echo': AbilityDependency('base', 'Echo Server'),
    'pcapwriter': AbilityDependency('base', 'Save to Pcap'),
    'pcapreader': AbilityDependency('base', 'Read from Pcap'),
    'demux': AbilityDependency('base', 'Demux'),
}


def get_classic(name):
    return classic_dependencies[name]
