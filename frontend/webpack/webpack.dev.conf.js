const webpack = require('webpack');
const path = require('path');

const HtmlWebpackPlugin = require('html-webpack-plugin');

module.exports = {
    mode: 'development',
    entry: {
        app: './app/main.js'
    },
    output: {
        path: __dirname,
        publicPath: '/',
        filename: '[name].js'
    },
    module: {
        rules: [
            { test: /\.vue$/, exclude: /node_modules/, enforce: 'pre', use: ['eslint-loader'] },
            { test: /\.vue$/, use: ['vue-loader'] },
            { test: /\.js$/, exclude: /node_modules/, enforce: 'pre', use: ['eslint-loader'] },
            { test: /\.js$/, exclude: /node_modules/, use: ['babel-loader'] },
            { test: /\.(png|jpg)$/, use: ['url-loader?limit=1'] },
            { test: /\.(woff2?|eot|ttf|otf|svg)(\?.*)?$/, loader: 'url-loader' },
            { test: /\.(css|scss)$/, use: ['style-loader', 'css-loader', 'sass-loader'] }
        ]
    },
    resolve: {
        extensions: ['.js', '.vue', '.json'],
        alias: {
            vue$: 'vue/dist/vue.esm.js',
            '@': path.join(__dirname, '..', 'app')
        }
    },
    devtool: '#source-map',
    plugins: [
        new HtmlWebpackPlugin({
            filename: 'index.html',
            template: './app/index.html',
            favicon: './app/assets/images/favicon.ico',
            inject: true
        }),
        new webpack.NamedModulesPlugin()
    ],
    devServer: {
        publicPath: '/',
        contentBase: './app',
        host: '127.0.0.1',
        port: 2442,
        proxy: {
            '/api': {
                target: undefined, // will be set by dev-mock and dev-server config
                secure: false
            }
        },
        headers: {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, PATCH, OPTIONS',
            'Access-Control-Allow-Headers': 'X-Requested-With, content-type, Authorization'
        }
    }
};