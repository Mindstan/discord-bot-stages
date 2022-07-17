FROM python:3.7-buster

RUN mkdir -p /var/www && chown -R www-data:www-data /var/www

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . /application
RUN chown -R www-data:www-data /application
WORKDIR /application


USER www-data
EXPOSE 80:80

CMD ["/bin/sh", "start.sh"]
