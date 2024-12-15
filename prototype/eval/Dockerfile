FROM python:3.6.9-alpine
WORKDIR ../
COPY . .
RUN apk add --no-cache --update-cache --update make automake gcc g++ subversion python3-dev git py3-scipy gfortran build-base wget libpng-dev openblas-dev

RUN pip install --upgrade pip

RUN pip install torch==1.8.1+cpu torchvision==0.9.1+cpu torchaudio==0.8.1 -f https://download.pytorch.org/whl/torch_stable.html

RUN pip install -r requirements.txt

ENTRYPOINT ["python","./run_attack.py"]