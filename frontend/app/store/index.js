import Vue from 'vue';
import Vuex from 'vuex';
Vue.use(Vuex);

import authStore from '@/store/auth';
import instanceStore from '@/store/instance';
import notebookStore from '@/store/notebook';

export default new Vuex.Store({
    modules: {
        instance: instanceStore,
        auth: authStore,
        notebook: notebookStore
    }
});