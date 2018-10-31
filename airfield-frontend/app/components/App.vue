<template>
    <div class="app">
        <app-toolbar></app-toolbar>
        <router-view></router-view>
        <app-toast></app-toast>
    </div>
</template>

<script>
    import AppToolbar from '@/components/AppToolbar';
    import AppToast from '@/components/AppToast';

    export default {
        components: {
            AppToolbar, AppToast
        }
    };
</script>