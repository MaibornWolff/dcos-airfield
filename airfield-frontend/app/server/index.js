import axios from 'axios';

const BASE_PATH = 'api/zeppelin/instance/';

export default {
    async getSecurityEnabled() {
        const { data: result } = await axios.get('/security');
        return result.data.securityEnabled;
    },
    async getDefaultConfigurations() {
        let path = BASE_PATH + 'configurations';
        const { data: result } = await axios.get(path);
        return result.data.configurations;
    },
    createNewInstance(configuration) {
        const parsedConfig = JSON.parse(JSON.stringify(configuration));
        if (parsedConfig.configuration.libraries[0].tensorflow){
            delete parsedConfig.configuration.libraries[0].tensorflow;
            parsedConfig.configuration.libraries[0].libraries.push('tensorflow');
        }
        return axios.post(BASE_PATH + 'create', configuration);
    },
    async getExistingInstances() {
        let path = BASE_PATH + 'retrieve/all';
        const { data: result } = await axios.get(path);
        return result.data.instances;
    },
    async getInstanceState(instanceId) {
        const { data: result } = await axios.get(BASE_PATH + 'state/' + instanceId);
        return result.data.instance_status;
    },
    triggerInstanceAction(action, instanceId) {
        const availableActions = ['start', 'restart', 'stop', 'delete'];
        if (!availableActions.includes(action)) {
            throw 'Action not supported: ' + action;
        }
        return axios.put(BASE_PATH + action + '/' + instanceId);
    }
};

