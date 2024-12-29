FROM wsong008/mab-malware
# copy the prototype to the container including the evaluation script
COPY minimal-prototype /root/minimal-prototype
COPY eval/evaluate.py /root/minimal-prototype/evaluate.py
COPY eval/evaluate.sh /root/minimal-prototype/evaluate.sh
COPY prototype/models /root/minimal-prototype/models

# copy data from original to the prototype
RUN cp -r /root/MAB-malware/data /root/minimal-prototype/data
# install bc for evaluation script
RUN apt install bc -y
