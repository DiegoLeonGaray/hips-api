FROM python:3.10-slim


RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app


COPY requirements.txt /usr/src/app/

RUN pip install numpy

RUN pip3 install -r requirements.txt

COPY . /usr/src/app

EXPOSE 8080

ENTRYPOINT ["python3"]

CMD ["-m", "swagger_server"]

RUN pip install llvmlite

RUN pip install numba

RUN pip install healpy

RUN pip install astropy

RUN pip install pandas






