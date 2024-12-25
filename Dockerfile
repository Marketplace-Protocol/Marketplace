# set base image (host OS)
FROM python:3.13

# set the working directory in the container
WORKDIR /Marketplace

# Set permissions on the definitions.json file
#COPY definitions.json /etc/rabbitmq/
#RUN chmod 600 /etc/rabbitmq/definitions.json


# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential python3-dev nginx && \
    rm -rf /var/lib/apt/lists/*

# copy the dependencies file to the working directory
COPY ./requirements.txt .

# install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# copy the content of the local src directory to the working directory
COPY ./ .

# Setting python path
ENV PYTHONPATH="${PYTHONPATH}:./application"

# command to run on container start
#CMD [ "python", "./application/app.py" ]
# with just wsgi
CMD ["gunicorn", "--workers", "2", "--bind", "0.0.0.0:5000", "app:flask_app"]
#CMD ["/bin/bash", "-c", "gunicorn --workers 3 --bind 0.0.0.0:5000 app:flask_app & nginx -g 'daemon off;'"]

