FROM nvidia/cuda:12.6.3-base-ubuntu20.04

# copy prototype to the container
COPY minimal-prototype/ /root/minimal-prototype/
COPY eval/evaluate.py /root/minimal-prototype/evaluate.py
COPY eval/evaluate.sh /root/minimal-prototype/evaluate.sh

# copy models to the container
COPY models/ /root/minimal-prototype/models/

# copy malware data to the container
COPY data/ /root/minimal-prototype/data/