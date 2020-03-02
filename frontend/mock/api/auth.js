/* eslint-disable camelcase */
const config = require('../config');
const app = require('../index');
const createResponse = require('../business/responseService').createResponse;


const DEFAULT_TIMEOUT = config.DEFAULT_TIMEOUT;
const BASE_PATH = '/' + config.BASE_PATH;
const SECURITY_PATH = config.SECURITY_PATH;
const username = config.username;

app.get([BASE_PATH, SECURITY_PATH, 'groups'].join('/'), function(req, res){ // get instance groups
    createResponse(res, 200, {
        groups: config.groups,
        oidc_activated: config.oidcActivated,
        dcos_groups_activated: config.dcosGroupsActivated
    }, DEFAULT_TIMEOUT / 2);
});


app.get([BASE_PATH, SECURITY_PATH, 'state'].join('/'), function(req, res){
    createResponse(res, 200, {
        authentication: true,
        isAuthenticated: true,
        username: username
    }, DEFAULT_TIMEOUT / 2);
});

console.info('Auth initialized.');