FROM python:3.7-buster

#RUN apt-get update && apt-get install -y gunicorn3
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"
COPY . /application
WORKDIR /application
RUN poetry install

EXPOSE 80:80

CMD ["/bin/sh", "start.sh"]
