const config = require('./webpack.dev.conf');

config.devServer.proxy['/api'].target = 'http://127.0.0.1:24420';

module.exports = config;