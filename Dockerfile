FROM python:3.12-alpine

LABEL maintainer="sile16"

RUN apk update && \
    apk add --upgrade git \
    && rm -rf /var/cache/apk/*

RUN mkdir -p /usr/share/pureswagger
ADD server/requirements.txt /usr/share/pureswagger/

RUN pip install --no-cache-dir -r /usr/share/pureswagger/requirements.txt 

#Get swagger-ui
RUN mkdir -p /usr/share/pureswagger/html
RUN git clone https://github.com/swagger-api/swagger-ui.git /swagger-ui && \
     cd /swagger-ui && \
     git checkout v5.17.4 && \
     cd && \
     mv /swagger-ui/dist/* /usr/share/pureswagger/html/    && \
     rm -rf /swagger-ui

ADD server /usr/share/pureswagger/

#this should overwrite the index.html provided in the cloned swagger-ui from master.
COPY html/ /usr/share/pureswagger/html/  
RUN rm -f /usr/share/pureswagger/html/.DS_Store

EXPOSE 5000

CMD ["python", "/usr/share/pureswagger/server.py"]

