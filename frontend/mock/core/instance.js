/* eslint-disable camelcase */
const TimeService = require('../business/timeService');
const DefaultConfigurations = require('../ressource/defaultConfigurations');
const config = require('../config');
const notebooks = require('./notebook');
const store = require('../storage/instance');
const copyService = require('../business/copyService');

const costCorePerMinute = config.costCorePerMinute;
const costGBPerMinute = config.costGBPerMinute;
const costTrackingEnabled = config.costTrackingEnabled;
const defaultConfiguration = DefaultConfigurations[1].configuration;


const instanceStates = {
    HEALTHY: 'HEALTHY',
    STOPPED: 'STOPPED',
    DEPLOYING: 'DEPLOYING',
    UNHEALTHY: 'UNHEALTHY',
    NOT_FOUND: 'NOT_FOUND',
    DELETED: 'DELETED'
};


function getRandomArrayElement(array) {
    return array[Math.floor(Math.random() * array.length)];
}

function getRandomState() {
    return getRandomArrayElement(Object.values(instanceStates));
}

function generateId() {
    return Math.random().toString(36).replace(/[^a-z]+/g, '');
}

function prepareConfiguration(configuration){
    if(configuration.delete_at){
        configuration.delete_at = TimeService.toSeconds(configuration.delete_at);
    }
    if(configuration.type === 'zeppelin'){
        const users = configuration.usermanagement.users;
        Object.keys(users).forEach(username => {
            if(!users[username]){
                users[username] = generateId();
            }
        });
    }
    else if(configuration.type === 'jupyter'){
        if(!configuration.usermanagement.password){
            configuration.usermanagement.password = generateId();
        }
    }
    return configuration;
}

function calculateCosts(instance){
    let coreMinutes = 0.0;
    let gbMinutes = 0.0;
    let runningTimeSeconds = 0;
    instance.runtimes.forEach(runtime => {
        const startedAt = runtime.started_at;
        const stoppedAt = runtime.stopped_at || TimeService.now();
        runningTimeSeconds += stoppedAt - startedAt;
        const minutes = (stoppedAt - startedAt) / 60.0;
        coreMinutes += runtime.cores * minutes;
        gbMinutes += (runtime.memory / 1024) * minutes;
    });
    const cost = costCorePerMinute * coreMinutes + costGBPerMinute * gbMinutes;
    return {
        cost: cost,
        running_time_seconds: runningTimeSeconds
    };
}

function createRuntimeObject(instanceConfiguration, startedAt = undefined, stoppedAt = undefined){
    const numExecutors = parseInt(instanceConfiguration.spark.cores_max / instanceConfiguration.spark.executor_cores, 10);
    return {
        started_at: startedAt,
        stopped_at: stoppedAt,
        cores: instanceConfiguration.notebook.cores + numExecutors * instanceConfiguration.spark.executor_cores,
        memory: instanceConfiguration.notebook.memory + numExecutors * instanceConfiguration.spark.executor_memory
    };
}

function calculateInstanceDetails(instance){
    const lastRunTime = instance.runtimes[instance.runtimes.length - 1];
    const startedAt = !lastRunTime.stopped_at ? TimeService.toIsoString(lastRunTime.started_at) : undefined;
    const details = {
        comment: instance.configuration.comment,
        created_by: instance.metadata.created_by,
        running_since: startedAt
    };
    if(instance.configuration.delete_at){
        details.delete_at = TimeService.toIsoString(instance.configuration.delete_at);
    }
    ['created_at', 'deleted_at'].forEach(key => {
        // noinspection TypeScriptValidateTypes
        if(instance.metadata[key]){
            // noinspection TypeScriptValidateTypes
            details[key] = TimeService.toIsoString(instance.metadata[key]);
        }
    });
    if(costTrackingEnabled){
        details.costs = calculateCosts(instance);
    }
    return details;
}

function prepareInstance(instanceConfiguration, createdBy, createdAt){
    const id = generateId();
    instanceConfiguration = prepareConfiguration(instanceConfiguration);
    const instance = {
        instance_id: id,
        status: instanceStates.DEPLOYING,
        deployment_stuck: false,
        stuck_duration: 0,
        proxy_url: '/proxy/' + id,
        configuration: instanceConfiguration,
        metadata: {
            created_by: createdBy,
            created_at: createdAt
        }
    };
    instance.runtimes = [createRuntimeObject(instanceConfiguration, createdAt)];
    return instance;
}

function generateUsermanagement(){
    return {
        enabled: Math.random() < 0.5,
        password: Math.random() < 0.5 ? '123456' : null,
        users: Math.random() < 0.5 ? { admin: 'admin', guest1: '123', guest2: '', guest3: '' } : {}
    };
}

function createGeneratedInstance() {
    const now = TimeService.now();
    const instanceConfiguration = copyService.copy(defaultConfiguration);
    instanceConfiguration.type = Math.random() < 0.5 ? 'jupyter' : 'zeppelin';
    instanceConfiguration.comment = getRandomArrayElement([
        'Lorem ipsum dolor sit amet',
        'consectetur adipiscing elit, sed do eiusmod tempor',
        'foobar',
        ''
    ]);
    instanceConfiguration.usermanagement = generateUsermanagement();
    const createdAt = now - 120; // -120 makes debugging of detecting stuck deployments easier
    const instance = prepareInstance(instanceConfiguration, 'Host', createdAt);
    instance.status = getRandomState();
    instance.status = [instanceStates.DELETED, instanceStates.NOT_FOUND].includes(instance.status) ? instanceStates.HEALTHY : instance.status;
    if (instance.status === instanceStates.DEPLOYING){
        instance.stuck_duration = now - createdAt;
        instance.deployment_stuck = true;
    }
    if(instance.status === instanceStates.STOPPED){
        instance.runtimes[0].stopped_at = createdAt;
    }
    return instance;
}




module.exports = {
    getDefaultConfigurations(){
        return DefaultConfigurations;
    },
    calculateCostsPerHour(configuration){
        const instance = {
            configuration: configuration,
            runtimes: [createRuntimeObject(configuration, 0, 3600)]
        };
        return calculateCosts(instance).cost;
    },
    
    getPrices(){
        return {
            cost_tracking_enabled: costTrackingEnabled,
            cost_currency: 'EURO',
            cost_core_per_minute: costCorePerMinute,
            cost_gb_per_minute: costGBPerMinute
        };
    },
    
    __startRuntime(instanceId){
        const instance = this.getInstance(instanceId, false);
        this.__finishRuntime(instanceId); // finishes runtime if necessary
        store.addRuntime(instanceId, createRuntimeObject(instance.configuration, TimeService.now()));
    },
    
    __finishRuntime(instanceId){
        const instance = this.getInstance(instanceId);
        const len = instance.runtimes.length;
        const runtime = instance.runtimes[len - 1];
        runtime.stopped_at = runtime.stopped_at !== undefined ? runtime.stopped_at : TimeService.now();
        store.updateLastRuntime(instanceId, runtime);
    },
    
    updateInstance(instanceId, configuration){
        store.updateInstanceConfiguration(instanceId, prepareConfiguration(configuration));
        store.updateStatus(instanceId, instanceStates.HEALTHY);
        this.__startRuntime(instanceId);
        this.__finishRuntime(instanceId);
    },
    
    addInstance(configuration, createdBy){
        const group = configuration.admin.group;
        if(config.oidcActivated && config.dcosGroupsActivated && !group){
            // A group must be set for an instance, if not 409 is thrown.
            return ['No group is selected! Please select a group to deploy the instance!', 409];
        }
        const instance = prepareInstance(configuration, createdBy, TimeService.now());
        instance.status = instanceStates.HEALTHY;
        store.addInstance(instance, false);
        return['', 200];
    },
    
    getInstances(deleted = false){
        const instances = [];
        store.getInstances(deleted).forEach(instance => instances.push(this.getInstanceDetails(instance.instance_id, deleted)));
        return instances;
    },
    
    getInstance(instanceId, deleted = false) {
        return store.getInstance(instanceId, deleted) || {};
    },
    
    getInstanceDetails(instanceId, deleted = false){
        const instance = this.getInstance(instanceId, deleted);
        const instanceDetails = this.getStatus(instanceId, deleted);
        instanceDetails.proxy_url = instance.proxy_url;
        instanceDetails.details = calculateInstanceDetails(instance);
        return instanceDetails;
    },

    getStatus(instanceId, deleted = false) {
        let instance = {};
        try{
            instance = this.getInstance(instanceId, deleted);
        }
        catch (e){
            console.error(e);
            instance.status = instanceStates.NOT_FOUND;
        }
        const deploying = instance.status === instanceStates.DEPLOYING;
        instance.deployment_stuck = deploying ? Math.random() >= 0.5 : false;
        instance.stuck_duration = TimeService.formatRunningTime(deploying ? Math.round(Math.random() * 10) : 0);
        return {
            instance_id: instanceId,
            status: instance.status,
            stuck_duration: instance.stuck_duration,
            deployment_stuck: instance.deployment_stuck
        };
    },

    action(action, instanceId) {
        switch (action) {
            case 'start':
            case 'restart':
                store.updateStatus(instanceId, instanceStates.HEALTHY);
                this.__finishRuntime(instanceId);
                this.__startRuntime(instanceId);
                break;

            case 'stop':
                store.updateStatus(instanceId, instanceStates.STOPPED);
                this.__finishRuntime(instanceId);
                break;

            case 'delete':
                this.__finishRuntime(instanceId);
                const instance = this.getInstance(instanceId);
                store.updateStatus(instanceId, instanceStates.DELETED);
                instance.metadata.deleted_at = TimeService.now();
                store.addInstance(instance, true);
                store.deleteInstance(instanceId, false);
                break;
            default:
                console.log('Action not accepted: ' + action); // eslint-disable-line
                break;
        }
    },
    
    getInstanceCredentials(instanceId){
        const instanceConfiguration = this.getInstance(instanceId).configuration;
        let instanceCredentials = [];
        if(!(instanceConfiguration.usermanagement.enabled)){
            return instanceCredentials;
        }
        if(instanceConfiguration.type === 'zeppelin'){
            instanceCredentials = instanceConfiguration.usermanagement.users;
        }
        else if(instanceConfiguration.type === 'jupyter'){
            instanceCredentials = instanceConfiguration.usermanagement.password;
        }
        else {
            throw Error('Unknown instance type: ' + instanceConfiguration.type);
        }
        return instanceCredentials;
    }
};


for (let i = 0, l = Math.round(Math.random() * 10 + 5); i < l; ++i) {
    const instance = createGeneratedInstance();
    for (let j = 0, k = Math.round(Math.random() * 10 + 3); j < k; ++j){
        notebooks.addNotebook({ instanceId: instance.instance_id });
    }
    store.addInstance(instance, false);
}

console.info(`${store.getInstances(false).length} instances created.`);

