FROM python:3.6

ENV FLASK_APP 'app'
ENV LC_ALL 'C.UTF-8'
ENV LANG 'C.UTF-8'

# copy codebase
ENV BASEDIR "/dcos-airfield"
RUN mkdir -p $BASEDIR/airfield-frontend
COPY airfield-microservice/requirements.txt $BASEDIR/
RUN pip install -r $BASEDIR/requirements.txt
COPY airfield-frontend/dist $BASEDIR/airfield-frontend/dist
COPY airfield-microservice $BASEDIR/airfield-microservice

# start backend
WORKDIR $BASEDIR/airfield-microservice/


CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--timeout", "30", "app:create_app()"]
