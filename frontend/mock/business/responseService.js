const config = require('../config');

module.exports = {
    // eslint-disable-next-line no-shadow
    createResponse(response, status = 200, data = {}, timeout = config.DEFAULT_TIMEOUT){
        setTimeout(() => response.status(status).send(data), timeout);
    }
};