FROM wsong008/mab-malware

COPY minimal-prototype /root/minimal-prototype
COPY eval/evaluate.py /root/minimal-prototype/evaluate.py
COPY eval/evaluate.sh /root/minimal-prototype/evaluate.sh

RUN cp -r /root/MAB-malware/models /root/minimal-prototype/models
RUN cp -r /root/MAB-malware/data /root/minimal-prototype/data
