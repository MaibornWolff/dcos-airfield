import Server from '@/server/index';

const INSTANCE_PATH = Server.INSTANCE_PATH;
const axiosInstance = Server.axiosInstance;


export default {
    async getInstancePrices() {
        const response = await axiosInstance.get('instance_prices');
        return response.data;
    },
    
    async calculateCosts(instanceConfiguration){
        const response = await axiosInstance.get('instance_costs', { params: { configuration: instanceConfiguration } });
        return response.data.costs_per_hour;
    },
    
    async getDefaultConfigurations() {
        const response = await axiosInstance.get('instance_configurations');
        return response.data.configurations;
    },

    async createNewInstance(configuration) {
        let response;
        try{
            response = await axiosInstance.post(INSTANCE_PATH, { configuration: configuration });
        }
        catch (error){
            let message;
            if(error.response.data && error.response.data.msg){
                message = error.response.data.msg;
            }
            return { message: message, status: error.response.status };
        }
        return { status: response.status };
    },
    
    async updateInstance(configuration, instanceId){
        await axiosInstance.put([INSTANCE_PATH, instanceId].join('/'), { configuration: configuration });
    },

    async getInstances(deleted) {
        const params = { deleted: deleted };
        const response = await axiosInstance.get(INSTANCE_PATH, { params });
        return response.data.instances;
    },
    
    async getInstance(instanceId, deleted){
        const params = { deleted: deleted };
        const response = await axiosInstance.get([INSTANCE_PATH, instanceId, 'details'].join('/'), { params });
        return response.data;
    },

    async getInstanceConfiguration(instanceId) {
        const response = await axiosInstance.get([INSTANCE_PATH, instanceId, 'configuration'].join('/'));
        return response.data;
    },

    async getInstanceCredentials(instanceId) {
        const response = await axiosInstance.get([INSTANCE_PATH, instanceId, 'credentials'].join('/'));
        return response.data;
    },

    async getInstanceState(instanceId) {
        const response = await axiosInstance.get([INSTANCE_PATH, instanceId, 'state'].join('/'));
        return response.data;
    },

    async triggerInstanceAction(action, instanceId) {
        const availableActions = ['start', 'restart', 'stop', 'delete'];
        if (!availableActions.includes(action)) {
            throw 'Action not supported: ' + action;
        }
        if (action === 'delete') {
            await axiosInstance.delete([INSTANCE_PATH, instanceId].join('/'));
        }
        else {
            await axiosInstance.post([INSTANCE_PATH, instanceId, action].join('/'));
        }
    }
};