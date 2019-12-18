import Vue from 'vue';
Vue.config.devtools = process.env.NODE_ENV !== 'production'; // eslint-disable-line
Vue.config.productionTip = false;

import BootstrapVue from 'bootstrap-vue';
Vue.use(BootstrapVue);
import 'bootstrap-vue/dist/bootstrap-vue.css';

import '@/assets/styles/main.scss';
import '@/assets/images/icons';

import App from '@/components/App';
import $router from '@/routes';
import $store from '@/store';

Vue.prototype.$eventBus = new Vue();


new Vue({ // eslint-disable-line
    el: '#app',
    template: '<app></app>',
    components: { App },
    router: $router,
    store: $store
});