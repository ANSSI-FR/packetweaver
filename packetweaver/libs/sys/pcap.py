try:
    import pcapy
    HAS_PCAPY = True
except ImportError:
    HAS_PCAPY = False

import threading
import multiprocessing
import traceback
import time
import logging
logger_pcap = logging.getLogger(__name__)


def capture_thread(stop_evt, pkts_pipe, iface,
                   bpf=None, buf_access_timeout=0.01):
    try:
        logger_pcap.debug('Pcapy open_live call')
        h = pcapy.open_live(iface, 65535, 1, 1)
        # making h.next() call non blocking, (hdr=None, _) is returned instead
        h.setnonblock(1)
        if not isinstance(bpf, type(None)):
            h.setfilter(bpf)
        while not stop_evt.is_set():
            hdr, payld = h.next()
            # do not block on an empty packet buffer
            if hdr is not None:
                if not isinstance(hdr, type(None)):
                    pkts_pipe.send(payld)
            else:
                # wait some times before trying to access the buffer again
                time.sleep(buf_access_timeout)
        h.close()
        logger_pcap.debug('Pcapy open_live ended')
        h = None
    except(EOFError, IOError):
        logger_pcap.warning('Pcapy capture traffic failed')
        traceback.print_exc()
        stop_evt.set()


def start_capture(iface, bpf=None, in_pkt_pipe=None):
    stop_evt = threading.Event()
    if isinstance(in_pkt_pipe, type(None)):
        pp, cp = multiprocessing.Pipe()
        t = threading.Thread(target=capture_thread,
                             name='Packet Capture',
                             args=(stop_evt, cp, iface, bpf))
    else:
        pp = None
        t = threading.Thread(target=capture_thread,
                             name='Packet Capture',
                             args=(stop_evt, in_pkt_pipe, iface, bpf))

    t.start()
    logger_pcap.debug('Run pcapy capture thread on iface [{}]'.format(iface))
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
        target=sending_raw_traffic_thread, name='Raw Traffic Emitter',
        args=(stop_evt, poller, receiver, iface)
    )
    t.start()

    return t, stop_evt
