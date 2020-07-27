FROM python:3.7-buster

#RUN apt-get update && apt-get install -y gunicorn3
COPY . /application
WORKDIR /application
RUN pip install -r requirements.txt

EXPOSE 80:80

CMD ["/bin/sh", "start.sh"]
