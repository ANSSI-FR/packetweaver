import re
import random
import ipaddress
import pytest
import packetweaver.libs.gen.rand_draw as draw


@pytest.fixture(scope='session')
def rand():
    return draw.RandDraw(random)


class TestRandDraw:
    def is_valid_ip(self, ip):
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False


    @staticmethod
    def is_valid_mac(mac):
        return re.search("^([0-9a-f]{2}:){5}([0-9a-f]{2})$", mac, re.I) is not None

    @staticmethod
    def is_valid_str(s):
        return isinstance(s, str)

    def test_string(self, rand):
        assert self.is_valid_str(rand.string())

        s = rand.string(10)
        assert len(s) == 10 and self.is_valid_str(s)

    def test_ipv6(self, rand):
        assert self.is_valid_ip(rand.ipv6())

    def test_number(self, rand):
        n = rand.number()
        assert -10 <= n <= 10 and isinstance(n, int)

        n = rand.number(-1.25, 99)
        assert isinstance(n, float)

    def test_mac(self, rand):
        assert self.is_valid_mac(rand.mac())

        mac = rand.mac('01:00:5e:00-7f:*:*')
        assert self.is_valid_mac(mac)
        assert mac[0:9] == '01:00:5e:' and 0 <= int(mac[9:11], 16) <= int('7f', 16)

        assert rand.mac('ff:ff:ff:ff:ff:ff') == 'ff:ff:ff:ff:ff:ff'

    def test_ipv4(self, rand):
        # validate standard cases
        assert rand.ipv4('192.168.0.1') == '192.168.0.1'

        ip = rand.ipv4('0-127.*.*.*')
        assert self.is_valid_ip(ip)
        assert 0 <= int(ip.split('.')[0]) <= 127

        ip = rand.ipv4()
        assert self.is_valid_ip(ip)

        ip = rand.ipv4('1-23.*.4.*')
        assert self.is_valid_ip(ip)
        assert 1 <= int(ip.split('.')[0]) <= 23
        assert int(ip.split('.')[2]) == 4

        # must fail returning None
        assert rand.ipv4('1') is None
        assert rand.ipv4('1-2-3.*.*.*') is None
        assert rand.ipv4('*.*.*') is None
        assert rand.ipv4('1234.*.*.*') is None
        assert rand.ipv4('-1.*.*.*') is None
