<template>
    <loading-spinner v-if="isLoading && initLoading" class="mt-3"></loading-spinner>
    <b-card v-else class="m-3">
        <div slot="header" class="cardHeader">
            <div class="cardTitle">
                <fa icon="list"></fa>
                <b>{{ existingInstancesLoaded ? 'Existing Instances' : 'Deleted Instances' }}</b>
            </div>

            <div>
                <b-button size="sm" @click="displayInstances">
                    <fa icon="spinner"></fa>
                    {{ existingInstancesLoaded ? 'Show deleted instances' : 'Show existing instances' }}
                </b-button>
                
                <b-button size="sm" @click="resetAndReload">
                    <fa icon="sync"></fa>
                    Refresh
                </b-button>

                <b-button v-if="existingInstancesLoaded" size="sm" variant="primary" to="/add">
                    <fa icon="plus"></fa>
                    Add instance
                </b-button>
            </div>
        </div>

        <b-table v-if="existingInstancesLoaded" striped hover :items="existingInstances" :fields="fields" class="mt-4">
            <template slot="status" slot-scope="props">
                <span v-if="props.item.status">{{ props.item.status }}</span>
                <fa icon="spinner" spin v-else></fa>

                <span v-if="props.item.status === 'DEPLOYING' && props.item.deployment_stuck" class="pl-1">
                    <fa icon="exclamation-triangle" class="text-danger" v-b-tooltip.hover.right
                        :title="'Running for ' + props.item.stuck_duration + 'min, try redeploying with less resources'"></fa>
                </span>
            </template>
            <template slot="show_details" slot-scope="row">
                <b-button
                    size="sm"
                    variant="outline-info"
                    @click="row.toggleDetails"
                    class="mr-2">
                    {{ row.detailsShowing ? 'Hide' : 'Show' }} Details
                </b-button>
            </template>
            <existing-instance-details slot="row-details" slot-scope="row" :item="row.item"></existing-instance-details>

            <template slot="buttons" slot-scope="props">
                <instance-buttons :item="props.item"
                                  @show-export="$refs.exportModal.open(props.item.id)"
                                  @show-import="$refs.importModal.open(props.item.id)"
                                  @show-passwords="$refs.passwordsModal.open(props.item.configuration.users)"
                                  @load-existing-instances="loadExistingInstances(true)"
                                  @get-instance-state="getInstanceState(props.item)"></instance-buttons>
            </template>
            <template slot="url" slot-scope="props">
                <a target="_blank" :href="parseProxyURL(props.item.id)">{{ '/proxy/' + props.item.id }}</a>
            </template>
        </b-table>
        <b-table v-if="!existingInstancesLoaded" striped hover :items="deletedInstances" :fields="deletedInstancesField" class="mt-4">
            <template slot="deleted_at" slot-scope="row">
                {{ toUTCString(row.item.deleted_at) }}
            </template>
            <template slot="show_details" slot-scope="row">
                <b-button
                    size="sm"
                    variant="outline-info"
                    @click="row.toggleDetails"
                    class="mr-2">
                    {{ row.detailsShowing ? 'Hide' : 'Show' }} Details
                </b-button>
            </template>
            <existing-instance-details slot="row-details" slot-scope="row" :item="row.item"></existing-instance-details>
            <template slot="buttons" slot-scope="props">
                <instance-buttons :item="props.item"
                                  @load-deleted-instances="loadDeletedInstances()"></instance-buttons>
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
    import ExistingInstanceDetails from '@/components/existing/ExistingInstanceDetails';

    import TimeService from '@/business/timeService';

    const DEFAULT_STATE = 'NOT_FOUND';
    const PROXY_BASE_PATH = 'proxy';
    const BASE_PATH = 'http';

    export default {
        components: {
            ExistingInstanceDetails,
            ExportModal,
            LoadingSpinner,
            InstanceButtons,
            PasswordsModal,
            ImportModal
        },

        data() {
            return {
                initLoading: true,
                polling: null,
                isLoading: false,
                actionInProgress: {},
                existingInstancesLoaded: true,
                fields: [
                    {
                        key: 'id',
                        label: 'ID',
                        sortable: true
                    },
                    {
                        key: 'status',
                        label: 'Status'
                    },
                    {
                        key: 'comment',
                        label: 'Comment'
                    },
                    {
                        key: 'url',
                        label: 'URL'
                    },
                    {
                        key: 'show_details'
                    },
                    {
                        key: 'buttons',
                        label: ''
                    }
                ],
                deletedInstancesField: [
                    {
                        key: 'id',
                        label: 'ID',
                        sortable: true
                    },
                    {
                        key: 'deleted_at',
                        label: 'Deleted at',
                        sortable: true
                    },
                    {
                        key: 'comment',
                        label: 'Comment'
                    },
                    {
                        key: 'show_details'
                    },
                    {
                        key: 'buttons',
                        label: ''
                    }
                ]
            };
        },

        computed: {
            ...mapGetters(['existingInstances', 'deletedInstances'])
        },

        created() {
            this.loadAllInstances();
            this.pollStates();
        },

        beforeDestroy() {
            clearInterval(this.polling);
        },


        methods: {
            getProxyURLPrefix(){
                const url = window.location.href;
                const domain = url.split('#')[0];
                const domainParts = domain.split('/');
                domainParts.forEach(v => {
                    if(v.includes(BASE_PATH)){
                        v = BASE_PATH;
                    }
                });
                return domainParts.join('/');
            },
            
            parseProxyURL(instanceId){
                return this.getProxyURLPrefix() + PROXY_BASE_PATH + '/' + instanceId;
            },
            
            toUTCString(time){
                return TimeService.toUTCString(time);
            },
            
            async loadAllInstances(){
                this.isLoading = true;
                this.loadExistingInstances();
                this.loadDeletedInstances();
                this.isLoading = false;
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
                    if (!forceReload) {
                        this.isLoading = false;
                    }
                    this.initLoading = false;
                }
            },

            async loadDeletedInstances() {
                try {
                    await this.$store.dispatch('loadDeletedInstances');
                }
                catch (e) {
                    this.$eventBus.$emit('showErrorToast', 'Error loading deleted instances!');
                }
            },

            pollStates() {
                if(this.existingInstancesLoaded) {
                    this.polling = setInterval(() => {
                        this.loadExistingInstances(false);
                    }, 5000);
                    
                }
                else {
                    clearInterval(this.polling);
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
                if(this.existingInstancesLoaded){
                    this.loadExistingInstances(true);
                }
                else {
                    this.loadDeletedInstances();
                }
            },
            
            displayInstances() {
                this.existingInstancesLoaded = !this.existingInstancesLoaded;
                this.resetAndReload();
                this.pollStates();
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