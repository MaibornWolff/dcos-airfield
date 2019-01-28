<template>
    <div class="app">
        <app-toolbar></app-toolbar>
        <router-view v-if="!authentication || isAuthenticated"></router-view>
        <app-toast></app-toast>
    </div>
</template>

<script>
    import AppToolbar from '@/components/AppToolbar';
    import AppToast from '@/components/AppToast';

    import { mapState } from 'vuex';

    export default {
        components: {
            AppToolbar, AppToast
        },
        
        computed: {
            ...mapState({ authentication: state => state.auth.authentication,
                isAuthenticated: state => state.auth.isAuthenticated })
        }
    };
</script>