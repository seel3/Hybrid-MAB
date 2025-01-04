FROM wsong008/mab-malware
# copy the prototype to the container including the evaluation script
COPY minimal-prototype/ /root/minimal-prototype/
#COPY eval/evaluate.py /root/minimal-prototype/evaluate.py
COPY eval/evaluate.sh /root/minimal-prototype/evaluate.sh
#COPY models/ /root/minimal-prototype/models/

# copy data from original to the prototype
RUN cp -r /root/MAB-malware/data /root/minimal-prototype/data
RUN cp -r /root/MAB-malware/models /root/minimal-prototype/models

# install bc for evaluation script
RUN apt install bc -y

# upgrade environment so gpu support is added
RUN pip install --upgrade pip
RUN pip install --upgrade torch torchvision torchaudio