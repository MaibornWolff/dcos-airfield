<template>
    <b-navbar type="dark" variant="primary" toggleable="md">
        <b-navbar-brand>
            <b-link to="/">
                <!-- workaround so the image is loaded correctly -->
                <b-img :src="image" alt="Airfield" class="airfieldLogo"></b-img>
                <span class="title">Airfield</span>
            </b-link>
        </b-navbar-brand>
        <auth></auth>
    </b-navbar>
</template>


<script>
    import Auth from '@/components/Auth';
    import image from '@/assets/images/airfield_logo.png';
    
    export default {
        components: {
            Auth
        },
        
        data(){
            return { image };
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