const express = require('express');
const app = express();
app.use(express.json());

const existingInstances = require('./existingInstances');
const defaultConfigurations = require('./defaultConfigurations');

const BASE_PATH = '/api/zeppelin/instance/';
const DEFAULT_TIMEOUT = 1000;

app.get(BASE_PATH + 'configurations', function(req, res){
    setTimeout(() => res.json({
        status: 200,
        data: {
            configurations: defaultConfigurations
        } }), DEFAULT_TIMEOUT);
});

app.post(BASE_PATH + 'create', function(req, res){
    existingInstances.add(req.body);
    setTimeout(() => res.send(''), DEFAULT_TIMEOUT);
});

app.get(BASE_PATH + 'retrieve/all', function(req, res){
    setTimeout(() => res.json({
        status: 200,
        data: {
            instances: existingInstances.get()
        } }), DEFAULT_TIMEOUT);
});

app.get(BASE_PATH + 'state/*', function(req, res){
    const id = +req.path.split('/').pop();
    setTimeout(() => res.send({
        status: 200,
        data: {
            instance_status: existingInstances.getState(id) // eslint-disable-line
        }
    }), DEFAULT_TIMEOUT / 2);
});

app.get(BASE_PATH + '*/*', function(req, res){
    const pathParts = req.path.split('/');
    const id = +pathParts.pop();
    const action = pathParts.pop();
    existingInstances.action(action, id);
    setTimeout(() => res.send(''), DEFAULT_TIMEOUT);
});

app.listen(24420, () => console.info('Mock server up and running, listening on port 24420.')); // eslint-disable-line