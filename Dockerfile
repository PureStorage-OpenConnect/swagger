FROM amd64/python:alpine

LABEL maintainer="sile16"

ENV VERSION "v2.2.10"
ENV FOLDER "swagger-ui-2.2.10"
ENV API_URLS ""
ENV API_KEY "**None**"
ENV OAUTH_CLIENT_ID "**None**"
ENV OAUTH_CLIENT_SECRET "**None**"
ENV OAUTH_REALM "**None**"
ENV OAUTH_APP_NAME "**None**"
ENV OAUTH_ADDITIONAL_PARAMS "**None**"
ENV SWAGGER_JSON "/app/swagger.json"
ENV BASE_URL ""
ENV DEBIAN_FRONTEND "noninteractive"

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
     git checkout v3.10.0 && \
     cd && \
     mv /swagger-ui/dist/* /usr/share/pureswagger/html/    && \
     mv /swagger-ui/docker-run.sh /usr/share/pureswagger && \
     rm -rf /swagger-ui

ADD server /usr/share/pureswagger/

#this should overwrite the index.html provided in the cloned swagger-ui from master.
COPY html/ /usr/share/pureswagger/html/  
COPY docker-run.sh /usr/share/pureswagger/
RUN rm -f /usr/share/pureswagger/html/.DS_Store

EXPOSE 5000

CMD ["sh", "/usr/share/pureswagger/docker-run.sh"]

