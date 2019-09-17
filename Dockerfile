FROM tiangolo/meinheld-gunicorn:python3.6-alpine3.8

RUN pip install flask

RUN apk add --no-cache mlocate
RUN ln -s /usr/bin/locate /usr/sbin/mlocate

COPY ./app /app
