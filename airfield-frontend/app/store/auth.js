import Server from '@/server';

export default {
    state: {
        authentication: null,
        isAuthenticated: true,
        username: ''
    },

    
    actions: {
        async loadSecurityState({ commit, state }) {
            if (state.authentication !== null) { // this needs to be checked only once ever
                return state;
            }
            const data = await Server.getSecurityState().then(
                response => {
                    return response;
                });
            commit('SET_SECURITY_STATE', data);
            return state;
        }
    },
    
    mutations: {
        SET_SECURITY_STATE(state, data) {
            state.authentication = data.authentication;
            state.isAuthenticated = data.isAuthenticated;
            state.username = data.username;
        }
    }
};