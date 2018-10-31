import Vue from 'vue';
import VueRouter from 'vue-router';
Vue.use(VueRouter);

import AddInstance from '@/components/add/AddInstance';
import ExistingInstances from '@/components/existing/ExistingInstances';

export default new VueRouter({
    routes: [{
        path: '/',
        component: ExistingInstances
    }, {
        path: '/add',
        component: AddInstance
    }]
});