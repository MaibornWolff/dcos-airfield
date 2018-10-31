FROM ubuntu:16.04

ENV FLASK_APP 'app'

# install base dependencies
RUN apt-get update
RUN apt-get install -y curl python3
RUN curl -sL https://deb.nodesource.com/setup_8.x | bash -
RUN apt install -y nodejs
# Fix pip3 not found bug
RUN apt-get remove python3-pip
RUN apt-get install -y python3-pip
RUN apt-get install -y python3-dev libffi-dev libssl-dev libxml2-dev libxslt1-dev libjpeg8-dev zlib1g-dev

# copy codebase
RUN mkdir $HOME/dcos-airfield
COPY airfield-frontend $HOME/dcos-airfield/airfield-frontend
COPY airfield-microservice $HOME/dcos-airfield/airfield-microservice

# install additional libraries
WORKDIR $HOME/dcos-airfield/airfield-frontend
RUN rm -rf node_modules
RUN npm install
WORKDIR $HOME/dcos-airfield/airfield-microservice/
RUN pip3 install -r requirements.txt

# build frontend
WORKDIR $HOME/dcos-airfield/airfield-frontend
RUN npm run build

# start backend
WORKDIR $HOME/dcos-airfield/airfield-microservice/
ENV LC_ALL 'C.UTF-8'
ENV LANG 'C.UTF-8'

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:create_app()"]
