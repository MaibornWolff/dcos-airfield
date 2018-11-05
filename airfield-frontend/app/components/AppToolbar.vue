<template>
    <b-navbar type="dark" variant="primary">
        <b-navbar-brand>
            <b-link to="/">
                <img src="../assets/images/airfield_logo.png" alt="Airfield" class="airfieldLogo">
                <span class="title">Airfield</span>
            </b-link>
        </b-navbar-brand>
    </b-navbar>
</template>


<script>
    export default { };
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