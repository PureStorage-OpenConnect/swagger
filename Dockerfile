FROM python:3-alpine3.7

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

RUN apk update --no-cache && apk upgrade --no-cache && apk add --update --no-cache \
    git


#Get latest swagger-ui
RUN mkdir -p /usr/share/pureswagger/html
RUN git clone https://github.com/swagger-api/swagger-ui.git /swagger-ui && \
     mv /swagger-ui/dist/* /usr/share/pureswagger/html/    && \
     mv /swagger-ui/docker-run.sh /usr/share/pureswagger && \
     rm -rf /swagger-ui



RUN apk add --no-cache --update build-base && \
    pip install --no-cache-dir pdfminer.six && \
    apk del build-base

ADD rest_extract/requirements.txt /usr/share/pureswagger/
RUN pip install --no-cache-dir -r /usr/share/pureswagger/requirements.txt
ADD rest_extract /usr/share/pureswagger/


#this should overwrite the index.html provided in the cloned swagger-ui from master.

COPY html/index.html /usr/share/pureswagger/html/
COPY docker-run.sh /usr/share/pureswagger/

EXPOSE 5000

CMD ["sh", "/usr/share/pureswagger/docker-run.sh"]

