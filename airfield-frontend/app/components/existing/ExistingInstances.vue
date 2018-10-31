<template>
    <loading-spinner v-if="isLoading" class="mt-3"></loading-spinner>
    <b-card v-else class="m-3">
        <div slot="header" class="cardHeader">
            <div class="cardTitle">
                <fa icon="list"></fa>
                <b>Existing Instances</b>
            </div>

            <div>
                <b-button size="sm" @click="resetAndReload">
                    <fa icon="sync"></fa> Refresh
                </b-button>

                <b-button size="sm" variant="primary" to="/add">
                    <fa icon="plus"></fa>
                    Add instance
                </b-button>
            </div>
        </div>

        <b-table striped hover :items="existingInstances" :fields="fields" class="mt-4">
            <template slot="status" slot-scope="props">
                <span v-if="props.item.status">{{ props.item.status }}</span>
                <fa icon="spinner" spin v-else></fa>
            </template>

            <template slot="url" slot-scope="props">
                <a target="_blank" :href="props.value">{{ props.value }}</a>
            </template>

            <template slot="buttons" slot-scope="props">
                <b-button
                    v-for="action in actions" :key="action.key"
                    size="sm"
                    class="ml-1 mr-1"
                    :variant="action.variant"
                    :disabled="actionInProgress[props.item.id]"
                    @click="triggerAction(action, props.item)">
                    <fa :icon="action.icon"></fa>
                    {{ action.name }}
                </b-button>

                <fa icon="spinner" spin v-if="actionInProgress[props.item.id]"></fa>
            </template>
        </b-table>
    </b-card>
</template>


<script>
    import Vue from 'vue';
    import { mapGetters } from 'vuex';

    import LoadingSpinner from '@/components/LoadingSpinner';
    import Server from '@/server';

    const DEFAULT_STATE = 'NOT_FOUND';
    
    export default {
        components: {
            LoadingSpinner
        },

        data() {
            return {
                isLoading: false,
                actionInProgress: { },

                fields: [
                    { key: 'id', label: 'ID', sortable: true },
                    { key: 'status', label: 'Status' },
                    { key: 'comment', label: 'Comment' },
                    { key: 'url', label: 'URL' },
                    { key: 'buttons', label: '' }
                ],

                actions: [
                    { key: 'start', name: 'Start', variant: 'success', icon: 'play' },
                    { key: 'restart', name: 'Restart', variant: 'outline-success', icon: 'play-circle' },
                    { key: 'stop', name: 'Stop', variant: 'warning', icon: 'stop' },
                    { key: 'delete', name: 'Delete', variant: 'danger', icon: 'trash-alt' }
                ]
            };
        },

        computed: {
            ...mapGetters(['existingInstances'])
        },

        created() {
            this.loadExistingInstances();
        },

        methods: {
            loadToken() {
                this.$store.dispatch('LOAD_SECURITY_TOKEN');
            },
            async loadExistingInstances(forceReload = false) {
                if (!forceReload) {
                    this.isLoading = true;
                }
                try {
                    await this.$store.dispatch('loadExistingInstances', forceReload);
                    if (this.existingInstances.length > 0) {
                        this.getInstanceStates();
                    }
                }
                catch (e) {
                    this.$eventBus.$emit('showErrorToast', 'Error loading existing instances!');
                }
                finally {
                    this.isLoading = false;
                }
            },

            getInstanceStates() {
                for (const item of this.existingInstances) {
                    this.getInstanceState(item);
                }
            },

            async getInstanceState(item) {
                try {
                    const data = await Server.getInstanceState(item.id);
                    Vue.set(item, 'status', data);
                }
                catch (error) {
                    console.error(error); // eslint-disable-line
                    Vue.set(item, 'status', DEFAULT_STATE);
                }
            },
            
            resetAndReload() {
                this.loadExistingInstances(true);
            },

            async triggerAction(action, item) {
                try {
                    Vue.set(this.actionInProgress, item.id, true);
                    await Server.triggerInstanceAction(action.key, item.id);
                    this.$eventBus.$emit('showSuccessToast', `Action "${action.name}" executed successfully.`);
                    
                    if (action.key === 'delete') {
                        this.loadExistingInstances(true);
                    }
                    else {
                        Vue.set(item, 'status', '');
                        this.getInstanceState(item);
                    }
                }
                catch (e) {
                    this.$eventBus.$emit('showErrorToast', `Error executing action "${action.name}".`);
                }
                finally {
                    Vue.delete(this.actionInProgress, item.id);
                }
            }
        }
    };
</script>


<style lang="scss" scoped>
    .noDataText {
        font-weight: bold;
        text-align: center;
    }

    .cardHeader {
        display: flex;
        flex-direction: row;
        align-items: center;
        justify-content: space-between;
    }

    .cardTitle svg {
        margin-right: 7px;
    }

    .card-body {
        padding: 1.25rem 0;
    }
</style>