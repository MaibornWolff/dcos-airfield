const express = require('express');
const app = express();
app.use(express.json());

const existingInstances = require('./existingInstances');
const notebooks = require('./notebooks');
const defaultConfigurations = require('./defaultConfigurations');

const BASE_PATH = '/api/zeppelin';
const DEFAULT_TIMEOUT = 1000;

app.get(BASE_PATH + '/configurations', function(req, res){
    setTimeout(() => res.json({
        status: 200,
        data: {
            configurations: defaultConfigurations
        } }), DEFAULT_TIMEOUT);
});

app.get('/api/security', function(req, res){
    setTimeout(() => res.send({
        status: 200,
        data: {
            authentication: true,
            isAuthenticated: true,
            username: 'Alwin'
        }
    }), DEFAULT_TIMEOUT / 2);
});

app.post(BASE_PATH + '/instance', function(req, res){ // create instance
    existingInstances.updateOrAddInstance(req.body);
    setTimeout(() => res.send(''), DEFAULT_TIMEOUT);
});

app.get(BASE_PATH + '/instance', function(req, res){ // get all instances
    setTimeout(() => res.json({
        status: 200,
        data: {
            instances: existingInstances.get()
        } }), DEFAULT_TIMEOUT);
});

app.post(BASE_PATH + '/instance/*/action/*', function(req, res){ // actions
    const pathParts = req.path.split('/');
    const action = pathParts.pop();
    pathParts.pop();
    const id = pathParts.pop();
    existingInstances.action(action, id);
    setTimeout(() => res.send(''), DEFAULT_TIMEOUT);
});

app.delete(BASE_PATH + '/instance/*', function(req, res) { // delete action
    const pathParts = req.path.split('/');
    const id = pathParts.pop();
    existingInstances.action('delete', id);
    setTimeout(() => res.send(''), DEFAULT_TIMEOUT);
});

app.put(BASE_PATH + '/instance/*', function(req, res){ // redeploy
    existingInstances.updateOrAddInstance(req.body);
    setTimeout(() => res.send(''), DEFAULT_TIMEOUT);
});

app.get(BASE_PATH + '/instance/*/state', function(req, res){
    const pathParts = req.path.split('/');
    pathParts.pop();
    const id = pathParts.pop();
    const instanceStatus = existingInstances.getState(id);
    if (instanceStatus === 'DEPLOYING') {
        setTimeout(() => res.send({
            status: 200,
            data: {
                instance_status: instanceStatus, // eslint-disable-line
                deployment_stuck: Math.random() >= 0.5,
                stuck_duration: Math.round(Math.random() * 10)
            }
        }), DEFAULT_TIMEOUT / 2);
    }
    else {
        setTimeout(() => res.send({
            status: 200,
            data: {
                instance_status: (instanceStatus !== undefined) ? instanceStatus : 'NOT_FOUND'
            }
        }), DEFAULT_TIMEOUT / 2);
    }

});

app.get('/api/zeppelin/notebook', function(req, res) { // list in Airfield stored notebooks
    setTimeout(() => res.send({
        status: 200,
        data: {
            notebooks: notebooks.get()
        }
    }), DEFAULT_TIMEOUT / 2);
});

app.get(BASE_PATH + '/instance/*/notebook', function(req, res) { // list in instance stored notebooks
    const notebook = notebooks.generateNotebook();
    setTimeout(() => res.send({
        status: 200,
        data: {
            notebooks: [notebook]
        }
    }), DEFAULT_TIMEOUT / 2);
});

app.post(BASE_PATH + '/instance/*/notebook/*', function(req, res) { // import notebook to instance
    setTimeout(() => res.json({
        status: 200,
        data: {} }), DEFAULT_TIMEOUT);
});

app.post('/api/zeppelin/notebook', function(req, res) { // export notebook from instance
    const status_options = [409, 200];
    const instanceStatus = (req.query.force === 'true') ? 200 : status_options[Math.round(Math.random())];
    if (instanceStatus === 200) {
        const r = notebooks.addNotebook(req.body.data.notebookId);
        if (!r) {
            setTimeout(() => res.status(500).json({
                status: 500,
                data: { } }), DEFAULT_TIMEOUT);
        }
        else {
            setTimeout(() => res.json({
                status: instanceStatus,
                data: { } }), DEFAULT_TIMEOUT);
        }
    }
    else {
        setTimeout(() => res.status(instanceStatus).json({
            status: instanceStatus,
            data: { } }), DEFAULT_TIMEOUT);
    }

});

app.listen(24420, () => console.info('Mock server up and running, listening on port 24420.')); // eslint-disable-line