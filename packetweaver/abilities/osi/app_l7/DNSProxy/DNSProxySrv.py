# coding: utf8
import packetweaver.core.ns as ns
import struct

try:
    import dns
    import dns.zone as zone_parser
    import dns.name
    import dns.rdatatype
    import dns.rdataclass
    import dns.flags
    import dns.rrset
    import dns.message as message_parser
    HAS_DNSPYTHON = True
except ImportError:
    HAS_DNSPYTHON = False


class Ability(ns.ThreadedAbilityBase):
    _option_list = [
        ns.PathOpt(
            'fake_zone', must_exist=True, readable=True, is_dir=False,
            comment="Zone file containing the names for which a lie must be returned."
        ),
        ns.PathOpt(
            'policy_zone', must_exist=True, readable=True, is_dir=False, optional=True,
            comment="Zone file containing the policy to apply to incoming requests. If no match is found, there is an implicit FAKE policy"
        ),
        ns.BoolOpt('resolver', default=False, comment='Whether we are spoofing a resolver (or an authoritative server'),
        ns.BoolOpt(
            'authentic', default=False,
            comment='If resolver is true, our answers are flagged as authentic, unless checking is disabled'
        ),
        ns.BoolOpt('quiet', default=True, comment='Whether we should log stuff on error'),
    ]

    _info = ns.AbilityInfo(
        name='DNSProxy Server',
        description='DNSProxy "server", which answers lies',
        authors=['Florian Maury', ],
        tags=[ns.Tag.TCP_STACK_L5, ns.Tag.THREADED, ns.Tag.DNS],
        type=ns.AbilityType.COMPONENT
    )

    _dependencies = []

    FAKE_POLICY = 0
    SERVFAIL_POLICY = 1
    NXDOMAIN_POLICY = 2
    NODATA_POLICY = 3
    TCP_POLICY = 4
    PASSTHRU_POLICY = 5

    DECISION_DICT = {
        NODATA_POLICY: lambda self, *args, **kwargs: self._send_nodata(*args, **kwargs),
        NXDOMAIN_POLICY: lambda self, *args, **kwargs: self._send_nxdomain(*args, **kwargs),
        SERVFAIL_POLICY: lambda self, *args, **kwargs: self._send_servfail(*args, **kwargs),
        TCP_POLICY: lambda self, *args, **kwargs: self._send_truncated(*args, **kwargs),
        PASSTHRU_POLICY: lambda self, *args, **kwargs: self._send_passthru(*args, **kwargs),
        FAKE_POLICY: lambda self, *args, **kwargs: self._send_fake(*args, **kwargs),
    }

    @classmethod
    def check_preconditions(cls, module_factory):
        l = []
        if not HAS_DNSPYTHON:
            l.append('DNSPython support missing or broken. Please install dnspython or proceed to an update.')
        l += super(Ability, cls).check_preconditions(module_factory)
        return l

    def _parse_zones(self):
        try:
            pz = zone_parser.from_file(self.policy_zone, origin='.', relativize=False, check_origin=False)
        except:
            if not self.quiet:
                self._view.error('Invalid policy zone file')
            return None, None

        try:
            fz = zone_parser.from_file(self.fake_zone, origin='.', relativize=False, check_origin=False)
        except:
            if not self.quiet:
                self._view.error('Invalid fake zone file')
            return None, None
        return fz, pz

    def _find_zone_match(self, zone, name, rdtype):
        try:
            while name != dns.name.root:
                found_rrset = None
                try:
                    found_rrset = zone.find_rrset(name, rdtype)
                except KeyError:
                    pass
                if found_rrset is None:
                    try:
                        found_rrset = zone.find_rrset(name, dns.rdatatype.CNAME)
                    except KeyError:
                        pass
                if found_rrset is None:
                    try:
                        found_rrset = zone.find_rrset(name, dns.rdatatype.DNAME)
                    except KeyError:
                        pass
                if found_rrset is not None:
                    return found_rrset
                if name.labels[0] == '*':
                    name = name.parent()
                name = dns.name.Name(['*'] + list(name.parent().labels))
        except dns.name.NoParent:
            pass
        raise KeyError('No matching record for {} {}'.format(name, rdtype))

    def _set_flags(self, dns_msg):
        dns_msg.flags |= dns.flags.QR
        if self.resolver:
            if dns_msg.flags & dns.flags.RD != 0:
                dns_msg.flags |= dns.flags.RA

            # If flag AD and authentic are both set, then nothing happens, and this is all good
            if self.authentic:
                if dns_msg.ednsflags & dns.flags.DO != 0 and dns_msg.flags & dns.flags.CD == 0:
                    dns_msg.flags |= dns.flags.AD
            else:
                dns_msg.flags &= (2 ** 11) - 1 - dns.flags.AD  # Revert AD byte

        else:
            dns_msg.flags |= dns.flags.AA

    def _fake_answer(self, fz, metadata, dns_msg, fake_rrset):
        qdrrset = dns_msg.question[0]
        self._set_flags(dns_msg)

        if qdrrset.rdtype in [dns.rdatatype.NS, dns.rdatatype.MX, dns.rdatatype.SRV]:
            if qdrrset.rdtype in [dns.rdatatype.NS, dns.rdatatype.SRV]:
                names = [rr.target for rr in fake_rrset.items]
            elif qdrrset.rdtype == dns.rdatatype.MX:
                names = [rr.exchange for rr in fake_rrset.items]

            addr_rrset = []
            for name in names:
                try:
                    addr_rrset.append(self._find_zone_match(fz, name, dns.rdatatype.A))
                except KeyError:
                    pass
                try:
                    addr_rrset.append(self._find_zone_match(fz, name, dns.rdatatype.AAAA))
                except KeyError:
                    pass
            dns_msg.additional = addr_rrset

        dns_msg.answer.append(fake_rrset)
        self._send(
            '\x00{}{}{}'.format(
                struct.pack('!H', len(metadata)),
                metadata,
                dns_msg.to_wire()
            )
        )

    def _send_empty_response(self, metadata, parsed, rcode):
        parsed.set_rcode(rcode)
        parsed.answer = []
        parsed.authority = []
        parsed.additional = []
        self._send(
            '\x00{}{}{}'.format(
                struct.pack('!H', len(metadata)),
                metadata,
                str(parsed.to_wire())
            )
        )

    def _send_negative_answer(self, fz, metadata, parsed, rcode):
        self._set_flags(parsed)
        name = parsed.question[0].name
        forged_soa = dns.rrset.from_text(
            name, 3600*3,
            dns.rdataclass.IN, dns.rdatatype.from_text('SOA'),
            'ns1.{} hostmaster.{} 1 {} {} {} {}'.format(name.to_text(), name.to_text(), 3*3600, 3600, 86400*7, 3*3600)
        )
        parsed.set_rcode(rcode)
        parsed.answer = []
        parsed.authority = [forged_soa]
        parsed.additional = []
        self._send(
            '\x00{}{}{}'.format(
                struct.pack('!H', len(metadata)),
                metadata,
                str(parsed.to_wire())
            )
        )

    def _send_nodata(self, fz, metadata=None, parsed=None):
        if parsed is None or metadata is None:
            if not self.quiet:
                self._view.error('Parsed packet unavailable. Dropping')
            return
        self._send_negative_answer(fz, metadata, parsed, 0)

    def _send_nxdomain(self, fz, metadata=None, parsed=None):
        if parsed is None or metadata is None:
            if not self.quiet:
                self._view.error('Parsed packet unavailable. Dropping')
            return
        self._send_negative_answer(fz, metadata, parsed, 3)

    def _send_servfail(self, fz, metadata=None, parsed=None):
        if parsed is None or metadata is None:
            if not self.quiet:
                self._view.error('Parsed packet unavailable. Dropping')
            return

        self._set_flags(parsed)
        self._send_empty_response(metadata, parsed, 2)

    def _send_truncated(self, fz, metadata=None, parsed=None):
        if parsed is None or metadata is None:
            if not self.quiet:
                self._view.error('Parsed DNS message unavailable. Dropping')
            return

        self._set_flags(parsed)
        parsed.flags |= dns.flags.TC
        self._send_empty_response(metadata, parsed, 0)

    def _send_passthru(self, fz, metadata=None, raw=None, parsed=None):
        if (raw is None and parsed is None) or metadata is None:
            if not self.quiet:
                self._view.error('Raw DNS message unavailable. Dropping')

        self._send(
            '\xFF{}{}{}'.format(
                struct.pack('!H', len(metadata)),
                metadata,
                raw if raw is not None else str(parsed.to_wire())
            )
        )

    def _send_fake(self, fz, metadata=None, parsed=None):
        if parsed is None or metadata is None:
            if not self.quiet:
                self._view.error('Parsed DNS message unavailable. Dropping')
            return

        try:
            rrset = self._find_zone_match(fz, parsed.question[0].name, parsed.question[0].rdtype)
            if rrset.name.to_text().startswith('*'):
                rrset.name = parsed.question[0].name
            self._fake_answer(fz, metadata, parsed, rrset)
        except KeyError:
            if not self.quiet:
                self._view.error('Fake policy but not matching fake record. Dropping')
            return

    def _find_policy(self, pz, rrset):
        try:
            policy_rrset = self._find_zone_match(pz, rrset.name, dns.rdatatype.TXT)
            verdict = None
            for item in policy_rrset.items:
                for string in item.strings:
                    rrtype, policy = string.split(' ')
                    if rrtype == 'ANY' or dns.rdatatype.from_text(rrtype) == rrset.rdtype:
                        if policy == 'NXDOMAIN':
                            if rrtype == 'ANY':
                                verdict = self.NXDOMAIN_POLICY
                            elif verdict is None:
                                verdict = self.NODATA_POLICY
                        elif policy == 'NODATA':
                            verdict = self.NODATA_POLICY
                        elif policy == 'SERVFAIL':
                            verdict = self.SERVFAIL_POLICY
                        elif policy == 'PASSTHRU':
                            verdict = self.PASSTHRU_POLICY
                        elif policy == 'TCP':
                            verdict = self.TCP_POLICY
                        else:
                            # Policy == FAKE or whatever else
                            verdict = self.FAKE_POLICY
                    if verdict is not None:
                        return verdict
            return None
        except Exception as e:
            print e
            return None

    def _handle_query(self, metadata, data, fz, pz):
        try:
            dns_msg = message_parser.from_wire(data)
        except (message_parser.ShortHeader, message_parser.TrailingJunk, dns.name.BadLabelType):
            self._view.error('Error while parsing DNS message. Pass Thru policy applied.')
            self.DECISION_DICT[self.PASSTHRU_POLICY](self, fz, metadata=metadata, raw=data)
            return

        # Figuring out which policy to apply
        verdict = self._find_policy(pz, dns_msg.question[0])
        if verdict is None:
            self._view.error('Could not determine a verdict. Dropping.')
            return
        self.DECISION_DICT[verdict](self, fz, metadata=metadata, parsed=dns_msg)

    def main(self):
        fz, pz = self._parse_zones()
        if fz is None or pz is None:
            return

        try:
            while not self.is_stopped():
                if self._poll(0.05):
                    s = self._recv()
                    metadata_len, = struct.unpack('!H', s[:2])
                    metadata = s[2:metadata_len+2]
                    data = s[metadata_len+2:]
                    self._handle_query(metadata, data, fz, pz)
        except (IOError, EOFError):
            pass