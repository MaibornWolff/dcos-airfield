import Server from '@/server/notebook';
import Vue from 'vue';

export default {
    state: {
        storedNotebooks: [],
        instanceNotebooks: {}
    },

    getters: {
        storedNotebooks: state => state.storedNotebooks,
        instanceNotebooks: state => state.instanceNotebooks
    },

    actions: {
        resetAllNotebooks({ dispatch }){
            dispatch('resetStoredNotebooks');
            dispatch('resetInstanceNotebooks');
        },
        
        async loadStoredNotebooks({ commit, state }, forceReload = true) {
            if(forceReload || state.storedNotebooks.length === 0){
                commit('SET_STORED_INSTANCES', await Server.getNotebooks());
            }
        },
        
        resetStoredNotebooks({ commit }){
            commit('SET_STORED_INSTANCES', []);
        },
        
        resetInstanceNotebooks({ commit }){
            commit('SET_INSTANCE_NOTEBOOKS', {});
        },
        
        deleteInstanceNotebooks({ commit, state }, instanceId){
            if(state.instanceNotebooks[instanceId]){
                Vue.delete(state.instanceNotebooks, instanceId);
                commit('SET_INSTANCE_NOTEBOOKS', state.instanceNotebooks);
            }
        },
        
        async loadInstanceNotebooks({ commit, state, dispatch }, payload){
            let instanceId, forceReload = true;
            if(typeof payload === 'string'){
                payload = { instanceId: payload };
            }
            if(typeof payload === 'object'){
                instanceId = payload.instanceId;
                if(payload.forceReload !== undefined){
                    forceReload = payload.forceReload;
                }
            }
            else{
                throw Error('Payload type not supported!');
            }
            if(forceReload){
                await dispatch('deleteInstanceNotebooks', instanceId);
            }
            if(state.instanceNotebooks[instanceId]){
                return;
            }
            Vue.set(state.instanceNotebooks, instanceId, await Server.getInstanceNotebooks(instanceId));
            commit('SET_INSTANCE_NOTEBOOKS', state.instanceNotebooks);
        }
    },

    mutations: {
        SET_STORED_INSTANCES(state, data) {
            state.storedNotebooks = data;
        },

        SET_INSTANCE_NOTEBOOKS(state, data){
            state.instanceNotebooks = data;
        }
    }
};