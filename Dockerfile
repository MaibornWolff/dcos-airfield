FROM python:3.7

ENV FLASK_APP 'app'
ENV LC_ALL 'C.UTF-8'
ENV LANG 'C.UTF-8'

# copy codebase
ENV BASEDIR "/dcos-airfield"
RUN mkdir -p $BASEDIR/frontend
COPY requirements.txt $BASEDIR/
RUN pip install -r $BASEDIR/requirements.txt
COPY frontend/dist $BASEDIR/frontend/dist
COPY run.py $BASEDIR/run.py
COPY airfield $BASEDIR/airfield

# start backend
WORKDIR $BASEDIR/


CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--timeout", "30", "-k", "geventwebsocket.gunicorn.workers.GeventWebSocketWorker", "run:create_app()"]
