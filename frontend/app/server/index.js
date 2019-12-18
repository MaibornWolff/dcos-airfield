import axios from 'axios';

const BASE_PATH = 'api/zeppelin';

function configureTensorflow(clonedConfig) {
    if (clonedConfig.configuration.libraries[0].tensorflow){
        delete clonedConfig.configuration.libraries[0].tensorflow;
        clonedConfig.configuration.libraries[0].libraries.push('tensorflow');
    }
}

export default {
    async getDefaultConfigurations() {
        const { data: result } = await axios.get(BASE_PATH + '/configurations');
        return result.data.configurations;
    },

    async getZeppelinGroups() {
        const { data: result } = await axios.get(BASE_PATH + '/groups');
        return result.data;
    },

    async createNewInstance(configuration) {
        const clonedConfig = JSON.parse(JSON.stringify(configuration));
        configureTensorflow(clonedConfig);
        if (clonedConfig.created_at) {
            await axios.put(BASE_PATH + '/instance/' + clonedConfig.id, configuration);
        }
        else {
            await axios.post(BASE_PATH + '/instance', configuration);
        }
    },

    async commitInstance(configuration) {
        const clonedConfig = JSON.parse(JSON.stringify(configuration));
        configureTensorflow(clonedConfig);
        await axios.put(BASE_PATH + '/commit/' + clonedConfig.id, configuration);
    },
    
    async getSecurityState() {
        const { data: result } = await axios.get('/api/security'); // we never need authentication on this endpoint
        return result.data;
    },

    async getExistingInstances() {
        const { data: result } = await axios.get(BASE_PATH + '/instance');
        return result.data.instances;
    },
    
    async getDeletedInstances() {
        const { data: result } = await axios.get(BASE_PATH + '/deleted/instance');
        return result.data.instances;
    },

    async deleteInstanceFromDeletedInstances(instanceId) {
        await axios.delete(BASE_PATH + '/deleted/instance/' + instanceId);
    },

    async getInstanceState(instanceId) {
        const { data: result } = await axios.get(BASE_PATH + '/instance/' + instanceId + '/state');
        return result.data;
    },

    async triggerInstanceAction(action, instanceId) {
        const availableActions = ['start', 'restart', 'stop', 'delete'];
        if (!availableActions.includes(action)) {
            throw 'Action not supported: ' + action;
        }
        if (action === 'delete') {
            await axios.delete(BASE_PATH + '/instance/' + instanceId);
        }
        else {
            await axios.post([BASE_PATH, 'instance', instanceId, 'action', action].join('/'));
        }
    },

    async getNotebooks() {
        const { data: result } = await axios.get('api/zeppelin/notebook');
        return result.data;
    },
    
    async fetchLocalNotebooks(instanceId) {
        const { data: result } = await axios.get(BASE_PATH + '/instance/' + instanceId + '/notebook');
        return result.data;
    },

    async importNotebook(notebookId, instanceId) {
        await axios.post(BASE_PATH + '/instance/' + instanceId + '/notebook/' + notebookId)
            .then(function(response) {
                return response.status;
            }).catch(function(error) {
                console.error(error); // eslint-disable-line
                throw 'Notebook import failed';
            });
    },
    
    async deleteNotebook(notebookId) {
        await axios.delete('api/zeppelin/notebook/' + notebookId)
            .then(function(response) {
                return response.status;
            }).catch(function(error) {
                console.error(error); // eslint-disable-line
                throw 'Notebook delete failed';
            });
    },
    
    async exportNotebook(notebookId, notebookName, instanceId, force = false) {
        return await axios.post('api/zeppelin/notebook?force=' + force,
             { data: { instanceId: instanceId, name: notebookName, notebookId: notebookId } }).then(function(response) {
                 return response.status;
             }).catch(function(error) {
                 if (error.response.status === 409) {
                     return 409;
                 }
                console.error(error); // eslint-disable-line
                 throw 'Notebook export failed';
             });
    }
    
};