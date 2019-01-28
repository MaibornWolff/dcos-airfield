<template>
    <div class="buttonCol">
        <b-button
            v-for="action in actions" :key="action.key"
            size="sm"
            class="ml-1 mr-1"
            :variant="action.variant"
            :disabled="actionInProgress"
            @click="triggerAction(action)">
            <fa :icon="action.icon"></fa>
            {{ action.name }}
        </b-button>

        <b-button v-if="item.configuration.users.length > 0" variant="info" size="sm"
                  class="mx-1" @click="showPasswords()">
            <fa icon="lock-open"></fa> Passwords
        </b-button>
        <b-button v-if="item.status === 'HEALTHY'" size="sm" class="mx-1" variant="outline-primary" @click="triggerAction({key: 'import', name: 'import'})"><fa icon="download"></fa> Import</b-button>
        <b-button v-if="item.status === 'HEALTHY'" size="sm" class="mx-1" variant="outline-primary" @click="triggerAction({key: 'export', name: 'export'})"><fa icon="upload"></fa> Export</b-button>

        <fa icon="spinner" spin v-if="actionInProgress"></fa>
    </div>
</template>

<script>
    import Vue from 'vue';
    import Server from '@/server';

    export default {
        name: 'InstanceButtons',
        props: {
            item: {
                type: Object,
                required: true
            }
            
        },
        data() {
            return {
                isLoading: false,
                actionInProgress: false,

                actions: [
                    { key: 'start', name: 'Start', variant: 'success', icon: 'play' },
                    { key: 'restart', name: 'Restart', variant: 'outline-success', icon: 'play-circle' },
                    { key: 'stop', name: 'Stop', variant: 'warning', icon: 'stop' },
                    { key: 'delete', name: 'Delete', variant: 'danger', icon: 'trash-alt' },
                    { key: 'redeploy', name: 'Reconfigure', variant: 'outline-danger', icon: 'cog' }
                ]
            };
        },
        methods: {
            async triggerAction(action) {
                try {
                    Vue.set(this, 'actionInProgress', true);
                    if (action.key === 'redeploy') {
                        this.$router.push('/redeploy/' + this.item.id);
                    }
                    else if (action.key === 'import') {
                        this.$emit('show-import');
                    }
                    else if (action.key === 'export') {
                        this.$emit('show-export');
                    }
                    else {
                        await Server.triggerInstanceAction(action.key, this.item.id);
                        this.$eventBus.$emit('showSuccessToast', `Action "${action.name}" executed successfully.`);

                        if (action.key === 'delete') {
                            this.$emit('load-existing-instances');
                        }
                        else {
                            Vue.set(this.item, 'status', '');
                            this.$emit('get-instance-state', this.item);
                        }
                    }
                }
                catch (e) {
                    this.$eventBus.$emit('showErrorToast', `Error executing action "${action.name}". "${e}"`);
                }
                finally {
                    Vue.set(this, 'actionInProgress', false);
                }
            },
            showPasswords() {
                this.$emit('show-passwords');
            }
        }

        
    };
</script>

<style scoped>

</style>