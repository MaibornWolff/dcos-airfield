import Vue from 'vue';
import Vuex from 'vuex';
Vue.use(Vuex);

import store from '@/store/core';
import authStore from '@/store/auth';

export default new Vuex.Store({
    modules: {
        main: store,
        auth: authStore
    }
});