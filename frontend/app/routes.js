import Vue from 'vue';
import VueRouter from 'vue-router';
Vue.use(VueRouter);

import AddInstance from '@/components/add/AddInstance';
import ExistingInstances from '@/components/existing/ExistingInstances';
import RedeployInstance from '@/components/add/RedeployInstance';

export default new VueRouter({
    routes: [{
        path: '/',
        component: ExistingInstances
    }, {
        path: '/add',
        component: AddInstance
    }, {
        path: '/redeploy/:instance',
        component: RedeployInstance
    }]
});