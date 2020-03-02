<template>
    <div class="buttonCol">
        <b-dropdown ref="buttonDropdown" text="Actions" class="m-2" variant="primary" right size="sm" @click="toggle()">
            <b-dropdown-item-button
                v-for="action in actions" :key="action.key"
                size="sm"
                class="mx-1"
                :variant="action.variant"
                :disabled="actionInProgress"
                @click="triggerAction(action)"
            >
                <fa :icon="action.icon"></fa>
                {{ action.name }}
            </b-dropdown-item-button>
            <b-dropdown-item-button
                size="sm"
                class="mx-1"
                :variant="row.item._commit ? 'danger' : 'secondary'"
                :disabled="actionInProgress"
                @click="triggerAction({key:'commit', name:'Commit'})"
            >
                <fa :icon="row.item._commit ? 'comment-slash' : 'comment'"></fa>
                {{ row.item._commit ? 'Reset comment' : 'Commit' }}
            </b-dropdown-item-button>
            <b-dropdown-item-button
                size="sm"
                variant="info"
                @click="$emit('toggle-instance')"
                :disabled="actionInProgress"
                class="mx-1"
            >
                <fa :icon="row.detailsShowing ? 'eye-slash' : 'eye'"></fa>
                {{ row.detailsShowing ? 'Hide' : 'Show' }} Details
            </b-dropdown-item-button>
            <b-dropdown-item-button
                variant="info"
                size="sm"
                class="mx-1"
                :disabled="actionInProgress"
                @click="$emit('show-passwords')"
            >
                <fa icon="lock-open"></fa>
                Passwords
            </b-dropdown-item-button>
            <b-dropdown-item-button
                v-if="row.item.status === 'HEALTHY'"
                size="sm"
                class="mx-1"
                variant="primary"
                :disabled="actionInProgress"
                @click="$emit('show-notebooks')"
            >
                <fa icon="laptop"></fa>
                Notebooks
            </b-dropdown-item-button>
        </b-dropdown>
        <fa icon="spinner" spin v-if="actionInProgress"></fa>
    </div>
</template>

<script>
    import Vue from 'vue';
    
    import Server from '@/server/instance';

    export default {
        name: 'InstanceButtons',
        props: {
            row: {
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
                    { key: 'restart', name: 'Restart', variant: 'success', icon: 'play-circle' },
                    { key: 'stop', name: 'Stop', variant: 'warning', icon: 'stop' },
                    { key: 'delete', name: 'Delete', variant: 'danger', icon: 'trash-alt' },
                    { key: 'redeploy', name: 'Reconfigure', variant: 'danger', icon: 'cog' }
                ]
            };
        },

        methods: {
            async triggerAction(action) {
                const id = this.row.item.instance_id;
                this.actionInProgress = true;
                try {
                    switch(action.key){
                        case 'commit':
                            await this.$emit('commit');
                            break;
                        case 'redeploy':
                            this.$router.push('/redeploy/' + id);
                            break;
                        default:
                            Vue.set(this.row.item, 'status', '');
                            await Server.triggerInstanceAction(action.key, id);
                            this.$eventBus.$emit('showSuccessToast', `Action "${action.name}" executed successfully.`);

                            if (action.key === 'delete') {
                                this.$emit('load-all-instances');
                            }
                            else {
                                this.$emit('reload-instance-details', this.row.item.instance_id);
                            }
                    }
                }
                catch (e) {
                    const msg = e.response.status === 403 ? e.response.data.msg : '';
                    this.$eventBus.$emit('showErrorToast', `Error executing action "${action.name}". ${msg}`);
                }
                finally {
                    this.actionInProgress = false;
                }
            }
        }

        
    };
</script>

<style lang="scss" scoped>
    .buttonCol{
        .m-2 {
            .mx-1:hover {
                background: black;
            }
        }
    }

</style>