import Vue from 'vue';
import VueRouter from 'vue-router';
Vue.use(VueRouter);

import Instances from '@/components/instances/Instances';
import ConfigureInstance from '@/components/configure/ConfigureInstance';

export default new VueRouter({
    routes: [{
        path: '/',
        component: Instances
    }, {
        path: '/add',
        component: ConfigureInstance
    }, {
        path: '/redeploy/:instance',
        component: ConfigureInstance
    }]
});