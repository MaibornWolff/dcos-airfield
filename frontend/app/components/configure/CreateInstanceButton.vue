<template>
    <div>
        <b-button
            :variant="isSelectedInstanceExisting ? 'outline-danger':'primary'"
            :disabled="isLoading"
            @click="createNewInstance"
        >
            <fa :icon="buttonIcon" :spin="isLoading"></fa>
            <template v-if="isSelectedInstanceExisting">
                Redeploy instance
            </template>
            <template v-else>
                Create new instance
            </template>
        </b-button>
        <confirmation-modal
            ref="confirmation"
            ok-variant="primary"
            :message="message"
            @ok="$emit('select-administration-tab')"
        >
        </confirmation-modal>
    </div>
</template>


<script>
    import { mapGetters } from 'vuex';

    import ConfirmationModal from '@/components/ConfirmationModal';

    import Server from '@/server/instance';
    
    export default {
        components: {
            ConfirmationModal
        },
        
        data() {
            return {
                isLoading: false,
                message: ''
            };
        },

        computed: {
            ...mapGetters(['selectedNewInstance', 'isSelectedInstanceExisting', 'dcosGroupsActivated', 'oidcActivated', 'selectedNewInstanceId']),
            buttonIcon() {
                if (this.isLoading) {
                    return 'spinner';
                }
                return this.isSelectedInstanceExisting ? 'cog' : 'check';
            }
        },
        
        methods: {
            dismiss(){
                this.$refs.confirmation.hide();
            },
            
            reset(){
                this.$store.dispatch('resetNewInstance');
                this.$store.dispatch('resetInstances');
                this.$router.push('/');
            },
            
            async createNewInstance() {
                this.isLoading = true;
                const id = this.selectedNewInstanceId;
                try {
                    if(this.isSelectedInstanceExisting){
                        await Server.updateInstance(this.selectedNewInstance, id);
                        this.$eventBus.$emit('showSuccessToast', `Instance ${id} updated successfully.`);
                        this.reset();
                    }
                    else {
                        const ret = await Server.createNewInstance(this.selectedNewInstance);
                        if(ret.status === 409){
                            this.message = ret.message;
                            this.$refs.confirmation.show();
                        }
                        else{
                            this.$eventBus.$emit('showSuccessToast', 'New instance created successfully.');
                            this.reset();
                        }
                    }
                }
                catch (e) {
                    if(this.isSelectedInstanceExisting){
                        this.$eventBus.$emit('showErrorToast', `Error updating the instance ${id}!`);
                    }
                    else {
                        this.$eventBus.$emit('showErrorToast', `Error creating the new instance!`);
                    }
                }
                finally {
                    this.isLoading = false;
                }
            }
        }
    };
</script>