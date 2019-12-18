<template>
    <b-navbar type="dark" variant="primary" toggleable="md">
        <b-navbar-brand>
            <b-link to="/">
                <img src="../assets/images/airfield_logo.png" alt="Airfield" class="airfieldLogo">
                <span class="title">Airfield</span>
            </b-link>
        </b-navbar-brand>
        <auth></auth>
    </b-navbar>
</template>


<script>
    import Auth from '@/components/Auth';
    
    export default {
        components: {
            Auth
        }
    };
</script>


<style lang="scss" scoped>
    @import "~@/assets/styles/variables";

    .airfieldLogo {
        width: 44px;
        display: inline-block;
        margin: -8px 10px -6px 0;
        vertical-align: text-bottom;
    }

    .title {
        font-family: 'Patua One';
        font-size: 24px;
        vertical-align: bottom;
        color: $color-white;
    }

    a {
        text-decoration: none;
    }
</style>