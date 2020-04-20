/* eslint-disable camelcase */
import Server from '@/server/instance';
import Vue from 'vue';


export default {
    state: {
        defaultConfigurations: [],
        selectedNewInstance: {},
        existingInstances: [],
        deletedInstances: [],
        instanceConfigurations: {},
        selectedNewInstanceId: '',
        costs: {}
    },

    getters: {
        defaultConfigurations: state => state.defaultConfigurations,
        selectedNewInstance: state => state.selectedNewInstance,
        isNewInstanceSelected: state => Object.keys(state.selectedNewInstance).length > 0,
        isSelectedInstanceExisting: state => state.selectedNewInstanceId !== '',
        existingInstances: state => state.existingInstances,
        deletedInstances: state => state.deletedInstances,
        instanceConfigurations: state => state.instanceConfigurations,
        selectedNewInstanceId: state => state.selectedNewInstanceId,
        costTrackingEnabled: state => state.costs.cost_tracking_enabled,
        costCurrency: state => state.costs.cost_currency,
        costCorePerMinute: state => state.costs.cost_core_per_minute,
        costGBPerMinute: state => state.costs.cost_gb_per_minute
    },

    actions: {
        async loadInstancePrices({ commit, state }){
            if(Object.keys(state.costs).length === 0){
                const prices = await Server.getInstancePrices();
                commit('SET_INSTANCE_PRICES', prices);
            }
        },
        
        async reloadInstance({ commit, state, dispatch }, payload){
            let instanceId, deleteConfiguration, reloadConfiguration, instance;
            if(typeof payload === 'string'){
                payload = { instanceId: payload };
            }
            if(typeof payload === 'object'){
                instanceId = payload.instanceId;
                reloadConfiguration = payload.reloadConfiguration !== undefined ? payload.reloadConfiguration : false;
                deleteConfiguration = payload.deleteConfiguration !== undefined ? payload.deleteConfiguration : true;
                if(reloadConfiguration){
                    deleteConfiguration = false;
                }
            }
            else{
                throw Error('Payload type not supported!');
            }
            const index = state.existingInstances.findIndex(v => v.instance_id === instanceId);
            if(deleteConfiguration){
                await dispatch('deleteInstanceConfiguration', instanceId);
            }
            if(reloadConfiguration){
                // So the configuration is not loaded unnecessary, but if needed it is loaded simultaneously.
                const responseList = await Promise.all([Server.getInstance(instanceId), dispatch('loadInstanceConfiguration', { instanceId, forceReload: reloadConfiguration })]);
                instance = responseList[0];
            }
            else{
                instance = await Server.getInstance(instanceId);
            }
            
            ['_showDetails', '_commit'].forEach(key => {
                instance[key] = state.existingInstances[index][key];
            });
            state.existingInstances.splice(index, 1, instance);
            commit('SET_EXISTING_INSTANCES', state.existingInstances);
        },
        
        async resetComment({ commit, state, dispatch }, instanceId){
            const index = state.existingInstances.findIndex(v => v.instance_id === instanceId);
            const instanceDetails = state.existingInstances[index];
            const comment = await dispatch('loadInstanceConfiguration', instanceId).then(
                response => {
                    return response.comment;
                });
            Vue.set(instanceDetails.details, 'comment', comment);
            commit('SET_EXISTING_INSTANCES', state.existingInstances);
        },

        async commitInstance({ state, dispatch, commit }, payload){
            const instanceId = payload.instanceId;
            const comment = payload.comment;
            const instanceConfiguration = await dispatch('loadInstanceConfiguration', instanceId);
            if(instanceConfiguration.comment !== comment){
                Vue.set(instanceConfiguration, 'comment', comment);
                await Server.updateInstance(instanceConfiguration, instanceId);
                commit('SET_INSTANCE_CONFIGURATIONS', state.instanceConfigurations);
                // runtimes will be updated, so a reload of the details is required. The configuration has only updates in the comment, so it isn't necessary to delete it.
                await dispatch('reloadInstance', { instanceId, deleteConfiguration: true, reloadConfiguration: true });
            }
        },
        
        setSelectedNewInstanceId({ commit }, instanceId){
            commit('SET_SELECTED_NEW_INSTANCE_ID', instanceId);
        },
        
        resetSelectedNewInstanceId({ commit }){
            commit('SET_SELECTED_NEW_INSTANCE_ID', '');
        },
        
        async loadDefaultConfigurations({ commit, state }) {
            if (state.defaultConfigurations.length > 0) {
                return;
            }
            const data = await Server.getDefaultConfigurations();
            data.forEach(instance => {
                instance.delete_at = instance.delete_at || '';
            });
            commit('SET_DEFAULT_CONFIGURATIONS', data);
        },

        selectNewInstance({ commit }, instance) {
            commit('SET_NEW_SELECTED_INSTANCE', instance);
        },
        
        async loadSelectedInstance({ dispatch }, instanceId){
            dispatch('setSelectedNewInstanceId', instanceId);
            dispatch('selectNewInstance', await dispatch('loadInstanceConfiguration', { instanceId, forceReload: true }));
        },

        async resetNewInstance({ state, dispatch }) {
            dispatch('selectNewInstance', {});
            dispatch('deleteInstanceConfiguration', state.selectedNewInstanceId);
            dispatch('resetSelectedNewInstanceId');
        },

        async loadExistingInstances({ commit, state, dispatch }, forceReload = false) {
            if (!forceReload && state.existingInstances.length > 0) {
                return false;
            }
            await dispatch('resetInstances');
            commit('SET_EXISTING_INSTANCES', await Server.getInstances(false));
            return true;
        },

        async loadDeletedInstances({ state, commit }, forceReload = false) {
            if(!forceReload && state.deletedInstances.length > 0){
                return;
            }
            const data = await Server.getInstances(true);
            commit('SET_DELETED_INSTANCES', data);
        },

        resetInstances({ commit, dispatch }) {
            dispatch('resetInstanceConfigurations');
            dispatch('resetAllNotebooks');
            commit('SET_EXISTING_INSTANCES', []);
        },

        resetInstanceConfigurations({ commit }){
            commit('SET_INSTANCE_CONFIGURATIONS', {});
        },
        
        deleteInstanceConfiguration({ commit, state }, instanceId){
            if(state.instanceConfigurations[instanceId]){
                Vue.delete(state.instanceConfigurations, instanceId);
                commit('SET_INSTANCE_CONFIGURATIONS', state.instanceConfigurations);
            }
        },
        
        async loadInstanceConfiguration({ commit, state, dispatch }, payload){
            let instanceId, forceReload;
            if(typeof payload === 'string'){
                payload = { instanceId: payload };
            }
            if(typeof payload === 'object'){
                instanceId = payload.instanceId;
                forceReload = payload.forceReload || false;
            }
            else{
                throw Error('Payload type not supported!');
            }
            if(forceReload){
                await dispatch('deleteInstanceConfiguration', instanceId);
            }
            if(!state.instanceConfigurations[instanceId]){
                Vue.set(state.instanceConfigurations, instanceId, await Server.getInstanceConfiguration(instanceId));
                commit('SET_INSTANCE_CONFIGURATIONS', state.instanceConfigurations);
            }
            return state.instanceConfigurations[instanceId];
        }
    },

    mutations: {
        SET_DEFAULT_CONFIGURATIONS(state, data) {
            state.defaultConfigurations = data;
        },

        SET_NEW_SELECTED_INSTANCE(state, data) {
            state.selectedNewInstance = data;
        },

        SET_EXISTING_INSTANCES(state, data) {
            state.existingInstances = data;
        },

        SET_DELETED_INSTANCES(state, data){
            state.deletedInstances = data;
        },

        SET_INSTANCE_CONFIGURATIONS(state, data){
            state.instanceConfigurations = data;
        },

        SET_SELECTED_NEW_INSTANCE_ID(state, data){
            state.selectedNewInstanceId = data;
        },

        SET_INSTANCE_PRICES(state, data){
            state.costs = data;
        }
    }
};