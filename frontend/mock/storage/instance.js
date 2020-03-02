const copyService = require('../business/copyService');

const deletedInstances = [];
const existingInstances = [];


module.exports = {
    getInstances(deleted){
        if(!deleted){
            return existingInstances;
        }
        return deletedInstances;
    },
    
    getInstance(instanceId, deleted){
        const item = copyService.copy(this.getInstances(deleted).find(instance => instance.instance_id === instanceId));
        if(item === undefined){
            throw Error(`The instance ${instanceId} does not exist!`);
        }
        return item;
    },
    
    __getIndexOfInstance(instanceId, deleted){
        const index = this.getInstances(deleted).findIndex(instance => instance.instance_id === instanceId);
        if(index === -1){
            throw Error(`The instance ${instanceId} does not exist!`);
        }
        return index;
    },

    updateInstanceConfiguration(instanceId, configuration){
        this.getInstances(false)[this.__getIndexOfInstance(instanceId, false)].configuration = copyService.copy(configuration);
    },

    updateStatus(instanceId, newStatus) {
        this.getInstances(false)[this.__getIndexOfInstance(instanceId, false)].status = newStatus;
    },
    
    updateLastRuntime(instanceId, runtime){
        const index = this.__getIndexOfInstance(instanceId);
        const len = this.getInstances(false)[index].runtimes.length;
        this.getInstances(false)[index].runtimes[len - 1] = copyService.copy(runtime);
    },
    
    addRuntime(instanceId, runtime){
        this.getInstances(false)[this.__getIndexOfInstance(instanceId)].runtimes.push(copyService.copy(runtime));
    },
    
    addInstance(instance, deleted){
        this.getInstances(deleted).push(copyService.copy(instance));
    },
    
    deleteInstance(instanceId, deleted){
        this.getInstances(deleted).splice(this.__getIndexOfInstance(instanceId, deleted), 1);
    }
};



