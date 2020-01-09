import Server from '@/server';

export default {
    state: {
        defaultConfigurations: [],
        selectedNewInstance: { },
        existingInstances: [],
        storedNotebooks: [],
        deletedInstances: []
    },

    getters: {
        defaultConfigurations: state => state.defaultConfigurations,
        selectedNewInstance: state => state.selectedNewInstance,
        isNewInstanceSelected: state => state.selectedNewInstance.hasOwnProperty('template_id'),
        existingInstances: state => state.existingInstances,
        storedNotebooks: state => state.storedNotebooks,
        deletedInstances: state => state.deletedInstances,
        zeppelinGroups: state => state.zeppelinGroups,
        oidcActivated: state => state.oidcActivated,
        dcosGroupsActivated: state => state.dcosGroupsActivated
    },

    actions: {
        async loadDefaultConfigurations({ commit, state }) {
            
            if (state.defaultConfigurations.length > 0) {
                return;
            }
            const data = await Server.getDefaultConfigurations().then(
                response => {
                    return response;
                });
            for (const instance of data) {
                instance.deleteAt = instance.deleteAt || '';
            }
            commit('SET_DEFAULT_CONFIGURATIONS', data);
        },
        
        async loadZeppelinGroups({ commit }) {
            const data = await Server.getZeppelinGroups().then(
                response => {
                    return response;
                });
            commit('SET_ZEPPELIN_GROUPS', data.groups);
            commit('SET_OIDC_ACTIVATED', data.oidc_activated);
            commit('SET_DCOS_GROUPS_ACTIVATED', data.dcos_groups_activated);
        },

        selectNewInstance({ commit }, instance) {
            commit('SET_NEW_SELECTED_INSTANCE', JSON.parse(JSON.stringify(instance)));
        },
        
        async findInstance({ commit, state }, instanceId) {
            if (state.existingInstances.length > 0) {
                let selectedInstance = {};
                for (const instance of state.existingInstances) {
                    if (instanceId === instance.id) {
                        selectedInstance = JSON.parse(JSON.stringify(instance));
                        if (selectedInstance.configuration.usermanagement === 'random') { // passwords have already been generated
                            selectedInstance.configuration.usermanagement = 'manual';
                        }
                        break;
                    }
                }
                commit('SET_NEW_SELECTED_INSTANCE', selectedInstance);
            }
        },

        resetNewInstance({ commit }) {
            commit('SET_NEW_SELECTED_INSTANCE', { });
        },

        async loadExistingInstances({ commit, state }, forceReload) {
            if (!forceReload && state.existingInstances.length > 0) {
                return;
            }
            const data = await Server.getExistingInstances().then(
                response => {
                    return response;
                });
            commit('SET_EXISTING_INSTANCES', data);
        },

        async loadDeletedInstances({ commit, state }) { // eslint-disable-line
            const data = await Server.getDeletedInstances().then(
                response => {
                    return response;
                });
            commit('SET_DELETED_INSTANCES', data);
        },

        resetExistingInstances({ commit }) {
            commit('SET_EXISTING_INSTANCES', []);
        },
        
        async loadStoredNotebooks({ commit }) {
            const data = await Server.getNotebooks().then(
                response => {
                    return response;
                });
            commit('SET_STORED_INSTANCES', data.notebooks);
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
        
        SET_STORED_INSTANCES(state, data) {
            state.storedNotebooks = data;
        },
        
        SET_DELETED_INSTANCES(state, data){
            state.deletedInstances = data;
        },

        SET_ZEPPELIN_GROUPS(state, data){
            state.zeppelinGroups = data;
        },

        SET_OIDC_ACTIVATED(state, data){
            state.oidcActivated = data;
        },

        SET_DCOS_GROUPS_ACTIVATED(state, data){
            state.dcosGroupsActivated = data;
        }
    }
};