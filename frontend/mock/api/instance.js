/* eslint-disable camelcase */
const instances = require('../core/instance');
const config = require('../config');
const app = require('../index');
const pathService = require('../business/pathService');
const createResponse = require('../business/responseService').createResponse;


const DEFAULT_TIMEOUT = config.DEFAULT_TIMEOUT;
const BASE_PATH = '/' + config.BASE_PATH;
const INSTANCE_PATH = config.INSTANCE_PATH;
const username = config.username;



app.get([BASE_PATH, 'instance_prices'].join('/'), function(req, res) { // get instance prices
    createResponse(res, 200, instances.getPrices());
});


app.get([BASE_PATH, 'instance_costs'].join('/'), function(req, res) { // calculate cost of the instance per hour
    createResponse(res, 200, {
        costs_per_hour: instances.calculateCostsPerHour(JSON.parse(req.query.configuration))
    });
});

app.get([BASE_PATH, 'instance_configurations'].join('/'), function(req, res){ // get default configurations
    createResponse(res, 200, {
        configurations: instances.getDefaultConfigurations()
    });
});

app.get([BASE_PATH, INSTANCE_PATH].join('/'), function(req, res){ // get all instances
    createResponse(res, 200, {
        instances: instances.getInstances(req.query.deleted === 'true')
    });
});

app.get([BASE_PATH, INSTANCE_PATH, '*', 'details'].join('/'), function(req, res){ // get instance details
    const id = pathService.getElementOfPath(req.path, 3);
    createResponse(res, 200, instances.getInstanceDetails(id, req.query.deleted === 'true'));
});

app.post([BASE_PATH, INSTANCE_PATH].join('/'), function(req, res){ // create instance
    const [msg, state] = instances.addInstance(req.body.configuration, username);
    createResponse(res, state, { msg: msg });
});

app.get([BASE_PATH, INSTANCE_PATH, '*', 'state'].join('/'), function(req, res){ // get instance status
    const id = pathService.getElementOfPath(req.path, 3);
    createResponse(res, 200, instances.getStatus(id), DEFAULT_TIMEOUT / 2);
});

app.get([BASE_PATH, INSTANCE_PATH, '*', 'configuration'].join('/'), function(req, res) { // get instance configuration
    const id = pathService.getElementOfPath(req.path, 3);
    createResponse(res, 200, instances.getInstance(id).configuration);
});

app.get([BASE_PATH, INSTANCE_PATH, '*', 'credentials'].join('/'), function(req, res) { // get instance credentials
    const id = pathService.getElementOfPath(req.path, 3);
    createResponse(res, 200, instances.getInstanceCredentials(id));
});

app.put([BASE_PATH, INSTANCE_PATH, '*'].join('/'), function(req, res){ // redeploy
    const id = pathService.getElementOfPath(req.path, 3);
    instances.updateInstance(id, req.body.configuration);
    createResponse(res);
});

app.delete([BASE_PATH, INSTANCE_PATH, '*'].join('/'), function(req, res) { // action: delete
    const id = pathService.getElementOfPath(req.path, 3);
    instances.action('delete', id);
    createResponse(res);
});

['start', 'restart', 'stop'].forEach(action => {
    app.post([BASE_PATH, INSTANCE_PATH, '*', action].join('/'), function(req, res){ // actions
        const id = pathService.getElementOfPath(req.path, 3);
        instances.action(action, id);
        createResponse(res, 200, { instance_id: id, status: action });
    });
});


console.info('Instance initialized.');