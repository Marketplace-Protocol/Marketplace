# set base image (host OS)
FROM python:3.13

# set the working directory in the container
WORKDIR /src

# copy the dependencies file to the working directory
COPY ./requirements.txt .

# install dependencies
RUN pip install -r requirements.txt

EXPOSE 8080

# copy the content of the local src directory to the working directory
COPY ./ .

# Setting python path
ENV PYTHONPATH="${PYTHONPATH}:./application"
# ENV PYTHONPATH "${PYTHONPATH}:./application"

# command to run on container start
CMD [ "python", "./application/app.py" ]