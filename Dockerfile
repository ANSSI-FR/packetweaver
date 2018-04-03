# Quick usage instructions:
# > sudo docker build -t pwdock .
# > sudo docker run -it pwdock bash
# root@xxxxxxxxxxxx:pw# ./run_pw
FROM debian:stable

# install all known dependencies
RUN apt-get update \
&& apt-get upgrade -y \
&& apt-get install -y vim git python python-pip graphviz python-ipaddress python-pyroute2 python-gmpy2 python-pcapy python-scapy
RUN pip install sphinx pylint sphinx_rtd_theme

# add packetweaver source code
WORKDIR /pw
ADD . .

# build documentation
WORKDIR packetweaver/doc
RUN make all

# go back to the "run_pw" directory
WORKDIR ../..

