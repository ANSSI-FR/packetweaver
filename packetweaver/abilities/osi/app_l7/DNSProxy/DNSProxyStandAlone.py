# coding: utf8
import packetweaver.core.ns as ns


class Ability(ns.ThreadedAbilityBase):
    _option_list = [
        ns.PathOpt('fake_zone', must_exist=True, readable=True, is_dir=False),
        ns.PathOpt('policy_zone', must_exist=True, readable=True, is_dir=False),
        ns.IpOpt(ns.OptNames.IP_SRC, default=None, optional=True),
        ns.IpOpt(ns.OptNames.IP_DST, default=None, optional=True),
        ns.PortOpt(ns.OptNames.PORT_DST, optional=True, default=53),
        ns.NICOpt(ns.OptNames.INPUT_INTERFACE),
        ns.NICOpt(ns.OptNames.OUTPUT_INTERFACE, default=None, optional=True),
        ns.BoolOpt('quiet', default=True)
    ]

    _info = ns.AbilityInfo(
        name='DNSProxy',
        description='Replacement for DNSProxy',
        authors=['Florian Maury', ],
        tags=[ns.Tag.TCP_STACK_L5, ns.Tag.THREADED, ns.Tag.DNS],
        type=ns.AbilityType.STANDALONE
    )

    _dependencies = [
        'mitm',
        ('dnsproxysrv', 'base', 'DNSProxy Server'),
        ('scapy_splitter', 'base', 'DNS Metadata Extractor'),
        ('scapy_unsplitter', 'base', 'DNS Metadata Reverser'),

    ]

    def main(self):
        dns_srv_abl = self.get_dependency(
            'dnsproxysrv', fake_zone=self.fake_zone, policy_zone=self.policy_zone, quiet=self.quiet
        )

        mitm_abl = self.get_dependency(
            'mitm', interface=self.interface, outerface=self.outerface, ip_src=self.ip_src, ip_dst=self.ip_dst,
            port_dst=self.port_dst, protocol='udp', mux=True
        )

        scapy_dns_metadata_splitter = self.get_dependency('scapy_splitter', quiet=self.quiet)
        scapy_dns_metadata_reverser = self.get_dependency('scapy_unsplitter', quiet=self.quiet)

        mitm_abl | scapy_dns_metadata_splitter | dns_srv_abl | scapy_dns_metadata_reverser | mitm_abl

        self._start_wait_and_stop(
            [dns_srv_abl, mitm_abl, scapy_dns_metadata_reverser, scapy_dns_metadata_splitter]
        )

    def howto(self):
        print("""This DNS proxy intercepts DNS requests at OSI layer 2. 
For each intercepted request, this proxy can either fake an answer and send it to the requester or forward
the request to the original recipient. Fake answers are authoritative, and they may contain DNS 
records for IPv4 or IPv6 addresses, denials of existence (nxdomain or empty answers), errors (SERVFAIL or 
truncated answer), NS records, MX records, and in fact whatever record you can think of. Special handling is
done for denials of existence, NS records, MX records, and SRV records, to either synthesize a SOA record or
add the corresponding glues whenever available.

Whether to fake answers is instructed through a DNS master file that contains policies.
Policies are formated as TXT records whose first word is the mnemonic of a record type (A, AAAA, NS, etc.) or 
the "ANY" keyword. ANY means all types of records. The second word is the policy decision. It can be one of the
following:
  * PASSTHRU: the request is forwarded, unaltered, to the original destination.
  * NODATA: the request is answered with the indication that there is no such DNS record for this record 
            type at the requested domain name.
  * NXDOMAIN: the request is answered with the indication that the requested domain name does not exist and that
              no records can be found at this name and under it. This policy only works only with the 
              keyword "ANY".
  * SERVFAIL: the request is answered with the indication that the server is unable to provide a valid answer
              at the moment. This will generally force implementations to retry the request against another 
              server, whenever possible.
  * TCP: the request is answered with an empty answer and the indication that the complete answer would 
         truncated. This will force RFC-compliant implementation to retry the request over TCP. TCP is currently
         unsupported by this ability.
  * FAKE: the request is answered with fake data as specified in the fake zone, as described hereunder.

The policy zone file must contain records whose owner name is fully qualified domain names. For instance, to
fake a request for the IPv4 address of ssi.gouv.fr, one would write in the policy file:
ssi.gouv.fr. IN TXT "A FAKE"

The policy zone file can use wildcards to cover all domain names under some domain name. For instance, to let
through all requests for all domain names under the fr TLD, one would write:
*.fr IN TXT "ANY PASSTHRU"

The wildcard matching is similar to that of the DNS. That means that if both previous policies are in the policy
file, all requests for any records and names under the fr TLD would be let through, save for a request for the 
IPv4 of ssi.gouv.fr. If two policies are defined for a given name (be it an ANY policy and a record 
type-specific policy or two ANY policies or even two exact match policies), the first record to match is used. 

Thus, one can write a default policy using the wildcard expression "*.". For instance, to answer that there is
no record for any NAPTR record, whatever the requested name is, and unless there is an explicit other policy to
apply, one would write:
*. IN TXT "NAPTR NODATA"

If no policy can be found for a domain name and a record type, the request is dropped. If the received request
cannot be parsed into a valid DNS message, the "packet" is let through. We think this is a reasonable behaviour,
because it might not be at all a DNS request.

The fake zone file is also a DNS master file containing all the records required to synthesize the fake answer, 
as instructed by the policy.
For instance, according to the previously described policy for ssi.gouv.fr IPv4, one would have to write 
something among the likes of:
ssi.gouv.fr. 3600 IN A 127.0.0.1

This would instruct this ability to answer "ssi.gouv.fr. A?" requests with a fake answer with a TTL of 1 hour,
and an IPv4 address equal to 127.0.0.1.
All domain names in the fake zone file must also be fully-qualified, and wildcards also apply, as described
before.

For example, the following files could be used:
---
Policy file:
---
*. IN TXT "NAPTR NODATA"
*.fr. IN TXT "ANY PASSTHRU"

ssi.gouv.fr. IN TXT "A FAKE"
ssi.gouv.fr. IN TXT "AAAA FAKE"
---
Fake zone file:
---
ssi.gouv.fr. 3600 IN A 127.0.0.1
ssi.gouv.fr. 7200 IN AAAA 2001:db8::1
---

The IP parameters and the destination port serves to better target the requests for which to answer fake 
records.
The input NIC is the network card connected to the victim. The output NIC is optional; it may be specified if 
the real DNS server is connected to a different card than the victim.
""")