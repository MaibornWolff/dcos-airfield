<template>
    <b-modal
        ref="confirmationModal"
        :title="title"
        :ok-variant="okVariant"
        :centered="centered"
        :header-class="headerClass"
        :footer-class="footerClass"
        :hide-header-close="hideHeaderClose"
        :size="size"
        auto-focus-button="ok"
        @ok="okClicked"
    >
        {{ message }}
    </b-modal>
</template>

<script>
    export default {
        name: 'ConfirmationModal',
        
        props: {
            title: {
                type: String,
                default: 'Confirmation'
            },
            okVariant: {
                type: String,
                default: 'primary'
            },
            centered: {
                type: Boolean,
                default: true
            },
            headerClass: {
                type: String,
                default: 'p-2 border-bottom-0'
            },
            footerClass: {
                type: String,
                default: 'p-2 border-top-0'
            },
            hideHeaderClose: {
                type: Boolean,
                default: true
            },
            size: {
                type: String,
                default: 'sm'
            },
            message: {
                type: String,
                default: ''
            }
            
        },
        methods: {
            show(){
                this.$refs.confirmationModal.show();
            },
            hide(){
                this.$refs.confirmationModal.hide();
            },
            okClicked(){
                this.$emit('ok');
            }
        }
    };
</script>

<style scoped>

</style>