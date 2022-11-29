FROM ghcr.io/maxotta/kiv-ds-docker:latest

RUN yum -q -y install python3
#RUN yum install make gcc wget openssl-devel bzip2-devel libffi-devel zlib-devel -y

RUN pip3 install flask
RUN pip3 install requests
RUN pip3 install kazoo

COPY python /opt/nodes
COPY terminal /opt/terminal

# CMD /usr/bin/python3 /opt/nodes/main.py

# EOF
