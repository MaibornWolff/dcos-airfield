import Server from '@/server';

export default {
    state: {
        securityEnabled: false,
        securityToken: '',
        defaultConfigurations: [],
        selectedNewInstance: { },

        existingInstances: []
    },

    getters: {
        securityEnabled: state => state.securityEnabled,
        defaultConfigurations: state => state.defaultConfigurations,
        selectedNewInstance: state => state.selectedNewInstance,
        isNewInstanceSelected: state => state.selectedNewInstance.hasOwnProperty('id'),

        existingInstances: state => state.existingInstances
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

        selectNewInstance({ commit }, instance) {
            commit('SET_NEW_SELECTED_INSTANCE', JSON.parse(JSON.stringify(instance)));
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

        resetExistingInstances({ commit }) {
            commit('SET_EXISTING_INSTANCES', []);
        }
    },

    mutations: {
        SET_SECURITY_ENABLED(state, data) {
            state.securityEnabled = data;
        },
        SET_DEFAULT_CONFIGURATIONS(state, data) {
            state.defaultConfigurations = data;
        },

        SET_NEW_SELECTED_INSTANCE(state, data) {
            state.selectedNewInstance = data;
        },

        SET_EXISTING_INSTANCES(state, data) {
            state.existingInstances = data;
        }
    }
};