import axios from 'axios';

const BASE_PATH = 'api/zeppelin/instance/';

export default {
    async getDefaultConfigurations() {
        const { data: result } = await axios.get(BASE_PATH + 'configurations');
        return result.data.configurations;
    },

    async createNewInstance(configuration) {
        const clonedConfig = JSON.parse(JSON.stringify(configuration));
        
        if (clonedConfig.configuration.libraries[0].tensorflow){
            delete clonedConfig.configuration.libraries[0].tensorflow;
            clonedConfig.configuration.libraries[0].libraries.push('tensorflow');
        }
        
        await axios.post(BASE_PATH + 'create', configuration);
    },

    async getExistingInstances() {
        const { data: result } = await axios.get(BASE_PATH + 'retrieve/all');
        return result.data.instances;
    },

    async getInstanceState(instanceId) {
        const { data: result } = await axios.get(BASE_PATH + 'state/' + instanceId);
        return result.data.instance_status;
    },

    async triggerInstanceAction(action, instanceId) {
        const availableActions = ['start', 'restart', 'stop', 'delete'];
        if (!availableActions.includes(action)) {
            throw 'Action not supported: ' + action;
        }
        await axios.put(BASE_PATH + action + '/' + instanceId);
    }
};