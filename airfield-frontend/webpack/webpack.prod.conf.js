const webpack = require('webpack');
const path = require('path');

const HtmlWebpackPlugin = require('html-webpack-plugin');
const ExtractTextPlugin = require('extract-text-webpack-plugin');
const OptimizeCSSPlugin = require('optimize-css-assets-webpack-plugin');
const UglifyJsPlugin = require('uglifyjs-webpack-plugin');

module.exports = {
    entry: {
        app: './app/main.js'
    },
    output: {
        path: path.resolve(__dirname, '../dist'),
        filename: 'files/js/[name].[chunkhash].js',
        chunkFilename: 'files/js/[name].[chunkhash].js',
        publicPath: '/'
    },
    module: {
        rules: [
            { test: /\.vue$/, loader: 'vue-loader', options: { extractCSS: true } },
            { test: /\.js$/, exclude: /node_modules/, loader: 'babel-loader' },
            { test: /\.(png|jpg)$/, loader: 'url-loader', options: {
                limit: 1,
                name: 'files/img/[name].[hash:7].[ext]'
            } },
            { test: /\.(woff2?|eot|ttf|otf|svg)(\?.*)?$/, loader: 'url-loader', options: {
                limit: 10000,
                name: 'files/fonts/[name].[hash:7].[ext]'
            } },
            { test: /\.(css|scss)$/, loader: ExtractTextPlugin.extract({
                fallback: 'style-loader',
                use: ['css-loader', 'sass-loader']
            }) }
        ]
    },
    resolve: {
        extensions: ['.js', '.vue', '.json'],
        alias: {
            vue$: 'vue/dist/vue.esm.js',
            '@': path.join(__dirname, '..', 'app')
        }
    },
    devtool: false,
    plugins: [
        new webpack.DefinePlugin({
            'process.env': {
                NODE_ENV: '"production"'
            }
        }),
        new UglifyJsPlugin(),
        new ExtractTextPlugin({
            filename: 'files/css/[name].[contenthash].css'
        }),
        new OptimizeCSSPlugin({
            cssProcessorOptions: {
                safe: true
            }
        }),
        new HtmlWebpackPlugin({
            filename: path.resolve(__dirname, '../dist/index.html'),
            template: './app/index.html',
            favicon: './app/assets/images/favicon.ico',
            inject: true,
            chunksSortMode: 'dependency',
            minify: {
                removeComments: true,
                collapseWhitespace: true,
                removeAttributeQuotes: true
            }
        }),
        new webpack.optimize.CommonsChunkPlugin({
            name: 'vendor',
            minChunks({ resource }) {
                return resource && /\.js$/.test(resource) && resource.includes('node_modules');
            }
        }),
        new webpack.optimize.CommonsChunkPlugin({
            name: 'manifest',
            chunks: ['vendor']
        })
    ]
};