/* eslint-disable camelcase */
const express = require('express');

const app = module.exports = express();

app.use(express.json());
const port = 24420;

require('./api/notebook');
require('./api/instance');
require('./api/auth');

app.listen(port, () => console.info(`Mock server up and running, listening on port ${port}.`));