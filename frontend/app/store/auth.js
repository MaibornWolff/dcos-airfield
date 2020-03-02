import Server from '@/server/auth';

export default {
    state: {
        authentication: null,
        isAuthenticated: true,
        username: '',
        dcosGroups: [],
        oidcActivated: false,
        dcosGroupsActivated: false
    },
    
    getters: {
        username: state => state.username,
        dcosGroups: state => state.dcosGroups,
        oidcActivated: state => state.oidcActivated,
        dcosGroupsActivated: state => state.dcosGroupsActivated
    },

    
    actions: {
        async loadDcosSettings({ commit }) {
            commit('SET_DCOS_SETTINGS', await Server.getZeppelinGroups());
        },
        
        async loadSecurityState({ commit, state }) {
            if (state.authentication !== null) { // this needs to be checked only once ever
                return state;
            }
            commit('SET_SECURITY_STATE', await Server.getSecurityState());
            return state;
        }
    },
    
    mutations: {
        SET_SECURITY_STATE(state, data) {
            state.authentication = data.authentication;
            state.isAuthenticated = data.isAuthenticated;
            state.username = data.username;
        },

        SET_DCOS_SETTINGS(state, data){
            state.dcosGroupsActivated = data.dcos_groups_activated;
            state.dcosGroups = data.groups;
            state.oidcActivated = data.oidc_activated;
        }
    }
};