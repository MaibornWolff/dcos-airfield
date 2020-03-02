/* eslint-disable camelcase */
const config = require('../config');
const app = require('../index');
const notebooks = require('../core/notebook');
const pathService = require('../business/pathService');
const createResponse = require('../business/responseService').createResponse;



const BASE_PATH = '/' + config.BASE_PATH;
const NOTEBOOK_PATH = config.NOTEBOOK_PATH;
const INSTANCE_PATH = config.INSTANCE_PATH;

app.get([BASE_PATH, NOTEBOOK_PATH].join('/'), function(req, res) { // list in Airfield stored notebooks
    createResponse(res, 200, {
        notebooks: notebooks.get()
    });
});

app.get([BASE_PATH, INSTANCE_PATH, '*', NOTEBOOK_PATH].join('/'), function(req, res) { // list in instance stored notebooks
    const instanceId = pathService.getElementOfPath(req.path, 3);
    createResponse(res, 200, {
        notebooks: notebooks.get(instanceId)
    });
});

app.post([BASE_PATH, NOTEBOOK_PATH, '*', 'import'].join('/'), function(req, res) { // import notebook to instance
    createResponse(res);
});

app.post([BASE_PATH, NOTEBOOK_PATH].join('/'), function(req, res) { // export notebook from instance
    const data = req.body.data;
    const payload = {
        notebookId: data.notebook_id,
        instanceId: data.instance_id
    };
    let notebookExists = false;
    if(!(req.query.force === 'true')){
        notebookExists = notebooks.notebookExists(payload);
    }
    if(notebookExists){
        createResponse(res, 409);
    }
    else {
        notebooks.addNotebook(payload);
        createResponse(res);
    }
});

app.delete([BASE_PATH, NOTEBOOK_PATH, '*'].join('/'), function(req, res) { // delete notebook from instance
    notebooks.deleteNotebook(pathService.getElementOfPath(req.path, 3));
    createResponse(res);
});

app.post([BASE_PATH, INSTANCE_PATH, '*', NOTEBOOK_PATH, 'backup'].join('/'), function(req, res) { // backup notebooks
    createResponse(res);
});

app.post([BASE_PATH, INSTANCE_PATH, '*', NOTEBOOK_PATH, 'restore'].join('/'), function(req, res) { // restore notebooks
    createResponse(res);
});

app.delete([BASE_PATH, INSTANCE_PATH, '*', NOTEBOOK_PATH, 'restore'].join('/'), function(req, res) { // cancel restore notebooks
    createResponse(res);
});


console.info('Notebook initialized.');