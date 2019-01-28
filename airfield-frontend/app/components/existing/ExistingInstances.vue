<template>
    <loading-spinner v-if="isLoading && initLoading" class="mt-3"></loading-spinner>
    <b-card v-else class="m-3">
        <div slot="header" class="cardHeader">
            <div class="cardTitle">
                <fa icon="list"></fa>
                <b>Existing Instances</b>
            </div>

            <div>
                <b-button size="sm" @click="resetAndReload">
                    <fa icon="sync"></fa>
                    Refresh
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
                
                <span v-if="props.item.status === 'DEPLOYING' && props.item.deployment_stuck" class="pl-1">
                    <fa icon="exclamation-triangle" class="text-danger" v-b-tooltip.hover.right :title="'Running for ' + props.item.stuck_duration + 'min, try redeploying with less resources'"></fa>
                </span>
            </template>

            <template slot="url" slot-scope="props">
                <a target="_blank" :href="props.value">{{ props.value }}</a>
            </template>

            <template slot="buttons" slot-scope="props" >
                <instance-buttons :item="props.item" @show-export="$refs.exportModal.open(props.item.id)" @show-import="$refs.importModal.open(props.item.id)" @show-passwords="$refs.passwordsModal.open(props.item.configuration.users)" @load-existing-instances="loadExistingInstances(true)" @get-instance-state="getInstanceState(props.item)"></instance-buttons>
            </template>
        </b-table>
        <passwords-modal ref="passwordsModal"></passwords-modal>
        <import-modal ref="importModal"></import-modal>
        <export-modal ref="exportModal"></export-modal>
    </b-card>
</template>


<script>
    import Vue from 'vue';
    import { mapGetters } from 'vuex';

    import LoadingSpinner from '@/components/LoadingSpinner';
    import InstanceButtons from '@/components/existing/InstanceButtons';
    import PasswordsModal from '@/components/existing/PasswordsModal';
    import ImportModal from '@/components/existing/ImportModal';
    import ExportModal from '@/components/existing/ExportModal';
    import Server from '@/server';

    const DEFAULT_STATE = 'NOT_FOUND';
    
    export default {
        components: {
            ExportModal, LoadingSpinner, InstanceButtons, PasswordsModal, ImportModal
        },

        data() {
            return {
                initLoading: true,
                polling: null,
                isLoading: false,
                actionInProgress: { },

                fields: [
                    { key: 'id', label: 'ID', sortable: true },
                    { key: 'status', label: 'Status' },
                    { key: 'comment', label: 'Comment' },
                    { key: 'url', label: 'URL' },
                    { key: 'buttons', label: '' }
                ]
            };
        },

        computed: {
            ...mapGetters(['existingInstances'])
        },

        created() {
            this.loadExistingInstances();
            this.pollStates();
        },

        beforeDestroy() {
            clearInterval(this.polling);
        },


        methods: {
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
                    this.initLoading = false;
                }
            },
            
            pollStates() {
                this.polling = setInterval(() => {
                    this.loadExistingInstances(false);
                }, 5000);
            },

            getInstanceStates() {
                for (const item of this.existingInstances) {
                    this.getInstanceState(item);
                }
            },

            async getInstanceState(item) {
                try {
                    const data = await Server.getInstanceState(item.id);
                    Vue.set(item, 'status', data.instance_status);
                    if (data.instance_status === 'DEPLOYING') {
                        Vue.set(item, 'deployment_stuck', data.deployment_stuck);
                        Vue.set(item, 'stuck_duration', data.stuck_duration);
                    }
                }
                catch (error) {
                    console.error(error); // eslint-disable-line
                    Vue.set(item, 'status', DEFAULT_STATE);
                }
            },
            
            resetAndReload() {
                this.loadExistingInstances(true);
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