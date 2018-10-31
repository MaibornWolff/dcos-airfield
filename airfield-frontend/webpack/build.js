/* eslint-disable no-console */

process.env.NODE_ENV = 'production';

const rm = require('rimraf');
const webpack = require('webpack');

const webpackConfig = require('./webpack.prod.conf');

console.info('\nBuilding for production...\n');

console.info('-> Deleting old build\n');
rm('./dist', error => {
    if (error) {
        throw error;
    }
    
    console.info('-> Applying webpack\n');
    webpack(webpackConfig, (wpError, stats) => {
        if (wpError) {
            throw wpError;
        }
        
        process.stdout.write(stats.toString({
            colors: true,
            modules: false,
            children: false,
            chunks: false,
            chunkModules: false
        }) + '\n\n');
        
        console.info('Build successful :)\n');
    });
});