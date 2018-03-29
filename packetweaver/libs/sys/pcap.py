try:
    import pcapy
    HAS_PCAPY = True
except ImportError:
    HAS_PCAPY = False

import threading
import multiprocessing

def capture_thread(stop_evt, pkts_pipe, iface, bpf=None):
    try:
        h = pcapy.open_live(iface, 65535, 1, 1)
        if not isinstance(bpf, type(None)):
            h.setfilter(bpf)

        while not stop_evt.is_set():
            hdr, payld = h.next()
            if not isinstance(hdr, type(None)):
                pkts_pipe.send(payld)
        h = None
    except(EOFError, IOError):
        stop_evt.set()


def start_capture(iface, bpf=None, in_pkt_pipe=None):
    stop_evt = threading.Event()
    if isinstance(in_pkt_pipe, type(None)):
        pp, cp = multiprocessing.Pipe()
        t = threading.Thread(target=capture_thread, name="Packet Capture", args=(stop_evt, cp, iface, bpf))
    else:
        pp = None
        t = threading.Thread(target=capture_thread, name="Packet Capture", args=(stop_evt, in_pkt_pipe, iface, bpf))
    t.start()
    return t, stop_evt, pp


def sending_raw_traffic_thread(stop_evt, poller, receiver, iface):
    h = pcapy.open_live(iface, 65535, 1, 1)
    while not stop_evt.is_set():
        if poller(0.1):
            try:
                s = receiver()
                h.sendpacket(s)
            except (EOFError, IOError):
                stop_evt.set()


def send_raw_traffic(iface, poller, receiver):
    stop_evt = threading.Event()
    t = threading.Thread(
        target=sending_raw_traffic_thread, name="Raw Traffic Emitter",
        args=(stop_evt, poller, receiver, iface)
    )
    t.start()

    return t, stop_evt

if __name__ == '__main__':
    import signal
    t, e, p = start_capture('br0', 'arp')
    signal.signal(signal.SIGINT, lambda s, f: e.set())
    cnt = 10
    pkt = p.recv()
    while cnt:
        print(pkt.encode('hex'))
        pkt = p.recv()
        cnt -= 1
    e.set()
    t.join()

