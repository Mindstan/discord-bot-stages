#!/bin/sh
docker stop progress-tracker
docker rm progress-tracker
docker run --name progress-tracker --env-file=env-vars -p 8008:80 progress-tracker
