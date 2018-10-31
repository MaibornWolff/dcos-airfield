import Vue from 'vue';
import Vuex from 'vuex';
Vue.use(Vuex);

import storeDefinition from '@/store/core';

export default new Vuex.Store(storeDefinition);