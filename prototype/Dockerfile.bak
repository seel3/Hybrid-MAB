FROM nvidia/cuda:12.6.3-base-ubuntu20.04

# copy prototype to the container
COPY minimal-prototype/ /root/minimal-prototype/
COPY eval/evaluate.sh /root/minimal-prototype/evaluate.sh

# copy models to the container
COPY models/ /root/minimal-prototype/models/

# copy malware data to the container
COPY data/ /root/minimal-prototype/data/

# set up requirements
RUN apt update && apt upgrade -y && apt install -y python3 python3-pip bc vim git
RUN python3 -m pip install -r /root/minimal-prototype/requirements.txt