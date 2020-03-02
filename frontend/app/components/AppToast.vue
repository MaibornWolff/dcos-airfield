<template>
    <b-alert
        :show="show"
        :variant="variant"
        dismissible
        @dismissed="dismiss"
    >
        {{ message }}
    </b-alert>
</template>


<script>
    const HIDE_TIMEOUT = 7000;

    export default {
        data() {
            return {
                variant: 'primary',
                message: '',
                show: false
            };
        },

        mounted() {
            this.$eventBus.$on('showInfoToast', message => this.open('primary', message));
            this.$eventBus.$on('showErrorToast', message => this.open('danger', message));
            this.$eventBus.$on('showWarningToast', message => this.open('warning', message));
            this.$eventBus.$on('showSuccessToast', message => this.open('success', message));
        },

        methods: {
            open(variant, message) {
                this.variant = variant;
                this.message = message;
                this.show = true;

                setTimeout(() => this.dismiss(), HIDE_TIMEOUT);
            },

            dismiss() {
                this.variant = 'primary';
                this.message = '';
                this.show = false;
            }
        }
    };
</script>


<style lang="scss" scoped>
    div {
        position: fixed;
        left: 15px;
        bottom: 15px;
        max-width: calc(100vw - 30px);
    }
</style>