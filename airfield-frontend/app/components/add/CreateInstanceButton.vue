<template>
    <b-button
        variant="primary"
        :disabled="isLoading"
        @click="createNewInstance">
        <fa :icon="isLoading ? 'spinner' : 'check'" :spin="isLoading"></fa>
        Create new instance
    </b-button>
</template>


<script>
    import { mapGetters } from 'vuex';

    import Server from '@/server';
    
    export default {
        data() {
            return {
                isLoading: false
            };
        },

        computed: {
            ...mapGetters(['selectedNewInstance'])
        },

        methods: {
            async createNewInstance() {
                try {
                    this.isLoading = true;
                    await Server.createNewInstance(this.selectedNewInstance);
                    this.$eventBus.$emit('showSuccessToast', 'New instance created successfully.');
                    this.$store.dispatch('resetNewInstance');
                    this.$store.dispatch('resetExistingInstances');
                }
                catch (e) {
                    this.$eventBus.$emit('showErrorToast', 'Error creating the new instance!');
                }
                finally {
                    this.isLoading = false;
                }
            }
        }
    };
</script>