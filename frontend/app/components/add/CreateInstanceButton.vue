<template>
    <b-button
        :variant="selectedNewInstance.created_at ? 'outline-danger':'primary'"
        :disabled="isLoading"
        @click="createNewInstance">
        <fa :icon="buttonIcon" :spin="isLoading"></fa>
        <template v-if="selectedNewInstance.created_at">Redeploy instance</template>
        <template v-else>Create new instance</template>
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
            ...mapGetters(['selectedNewInstance', 'dcosGroupsActivated', 'oidcActivated']),
            buttonIcon() {
                if (this.isLoading) {
                    return 'spinner';
                }
                return this.selectedNewInstance.created_at ? 'cog' : 'check';
            }
        },
        
        methods: {
            async createNewInstance() {
                if (!this.selectedNewInstance.configuration.group && this.dcosGroupsActivated && this.oidcActivated){
                    this.$eventBus.$emit('showErrorToast', 'No group is selected! Please select a group to deploy the instance!');
                    return;
                }
                try {
                    this.isLoading = true;
                    await Server.createNewInstance(this.selectedNewInstance);
                    this.$eventBus.$emit('showSuccessToast', 'New instance created successfully.');
                    this.$store.dispatch('resetNewInstance');
                    this.$store.dispatch('resetExistingInstances');
                    this.$router.push('/');
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