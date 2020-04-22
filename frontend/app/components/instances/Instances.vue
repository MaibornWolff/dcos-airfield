<template>
    <b-card class="m-3">
        <div slot="header" class="cardHeader">
            <div class="cardTitle">
                <fa icon="list"></fa>
                <b>
                    {{ existingInstancesLoaded ? 'Existing Instances' : 'Deleted Instances' }}
                    <fa icon="spinner" spin v-if="isLoading"></fa>
                </b>
            </div>
            <div>
                <b-button size="sm" @click="displayInstances">
                    <fa icon="spinner"></fa>
                    {{ existingInstancesLoaded ? 'Show deleted instances' : 'Show existing instances' }}
                </b-button>
                <b-button size="sm" @click="loadAllInstances(true)">
                    <fa icon="sync"></fa> Refresh
                </b-button>
                <b-button v-if="existingInstancesLoaded" size="sm" variant="primary" to="/add">
                    <fa icon="plus"></fa> Add instance
                </b-button>
            </div>
        </div>
        <b-card-body class="card-body">
            <template v-if="existingInstancesLoaded">
                <loading-spinner v-if="isLoading && existingInstances.length === 0" class="mt-3"></loading-spinner>
                <b-table v-else striped hover :items="existingInstances" :fields="fields" class="mt-4" primary-key="instance_id" sort-by="details.created_at" sort-desc>
                    <template v-slot:cell(status)="props">
                        <span v-if="props.item.status">{{ props.item.status }}</span>
                        <fa icon="spinner" spin v-else></fa>

                        <span v-if="props.item.status === 'DEPLOYING' && props.item.deployment_stuck" class="pl-1">
                            <fa icon="exclamation-triangle" class="text-danger" v-b-tooltip.hover.right
                                :title="'Running for ' + convertTimestamp(props.item.stuck_duration) + ', try redeploying with less resources'"
                            ></fa>
                        </span>
                    </template>
                    <template v-slot:cell(details.comment)="row">
                        <instance-comment :ref="'instanceComment' + row.item.instance_id" :row="row"></instance-comment>
                    </template>
                    <template v-slot:row-details="row">
                        <instance-details :existing-instance="existingInstancesLoaded" :item="row.item"></instance-details>
                    </template>
                    <template v-slot:cell(buttons)="props">
                        <instance-buttons :row="props"
                                          @show-notebooks="$refs.notebooksModal.open(props.item.instance_id)"
                                          @show-passwords="$refs.passwordsModal.open(props.item.instance_id)"
                                          @load-all-instances="loadAllInstances(true)"
                                          @reload-instance-details="reloadInstanceDetails(props.item.instance_id)"
                                          @commit="$refs['instanceComment' + props.item.instance_id].toggle()"
                                          @toggle-instance="toggleInstance(props)"
                        ></instance-buttons>
                    </template>
                    <template v-slot:cell(proxy_url)="data">
                        <a target="_blank" :href="parseProxyURL(data.value)">{{ data.value }}</a>
                    </template>
                </b-table>
            </template>
            <template v-if="!existingInstancesLoaded">
                <loading-spinner v-if="isLoading && deletedInstances.length === 0" class="mt-3"></loading-spinner>
                <b-table v-else striped hover :items="deletedInstances" :fields="deletedInstancesField" class="mt-4" sort-by="details.deleted_at" sort-desc>
                    <template v-slot:cell(show_details)="row">
                        <b-button
                            size="sm"
                            variant="outline-info"
                            @click="toggleInstance(row)"
                            class="mr-2"
                        >
                            <fa v-if="row.detailsShowing" :icon="row.detailsShowing ? 'eye-slash' : 'eye'"></fa>
                            {{ row.detailsShowing ? 'Hide' : 'Show' }} Details
                        </b-button>
                    </template>
                    <template v-slot:row-details="row">
                        <instance-details :existing-instance="existingInstancesLoaded" :item="row.item"></instance-details>
                    </template>
                </b-table>
            </template>
            <passwords-modal ref="passwordsModal"></passwords-modal>
            <notebooks-modal ref="notebooksModal"></notebooks-modal>
        </b-card-body>
    </b-card>
</template>


<script>
    import Vue from 'vue';
    import { mapGetters } from 'vuex';

    import LoadingSpinner from '@/components/LoadingSpinner';
    import InstanceButtons from '@/components/instances/InstanceButtons';
    import PasswordsModal from '@/components/instances/PasswordsModal';
    import NotebooksModal from '@/components/instances/NotebooksModal';
    import InstanceDetails from '@/components/instances/InstanceDetails';
    import InstanceComment from '@/components/instances/InstanceComment';

    import Server from '@/server/instance';
    import TimeService from '@/business/timeService';
    

    export default {
        components: {
            InstanceDetails,
            LoadingSpinner,
            InstanceButtons,
            PasswordsModal,
            NotebooksModal,
            InstanceComment
        },

        data() {
            return {
                DEFAULT_STATE: 'NOT_FOUND',
                polling: null,
                isLoading: false,
                existingInstancesLoaded: true,
                fields: [
                    { key: 'instance_id', label: 'ID', sortable: true },
                    { key: 'status', label: 'Status', sortable: true },
                    { key: 'details.created_at', label: 'Created at', sortable: true },
                    { key: 'details.comment', label: 'Comment', sortable: true },
                    { key: 'proxy_url', label: 'URL' },
                    { key: 'buttons', label: '' }
                ],
                deletedInstancesField: [
                    { key: 'instance_id', label: 'ID', sortable: true },
                    { key: 'details.deleted_at', label: 'Deleted at', sortable: true },
                    { key: 'details.comment', label: 'Comment', sortable: true },
                    { key: 'show_details', label: '' }
                ]
            };
        },

        computed: {
            ...mapGetters(['existingInstances', 'deletedInstances'])
        },

        created() {
            this.loadAllInstances(true);
            this.pollStates();
        },

        beforeDestroy() {
            clearInterval(this.polling);
        },


        methods: {
            convertTimestamp(time){
                return TimeService.humanizeTimestamp(time);
            },
            
            toggleInstance(row){
                row.toggleDetails();
                if(row.item._showDetails && this.existingInstancesLoaded){
                    this.reloadInstanceDetails(row.item.instance_id);
                }
            },
            
            async reloadInstanceDetails(instanceId){
                try{
                    await this.$store.dispatch('reloadInstance', { instanceId, deleteConfiguration: false });
                }
                catch(e) {
                    console.error(e);
                    this.$eventBus.$emit('showErrorToast', `Error reloading the instance ${instanceId}!`);
                }
            },
            
            parseProxyURL(proxyUrl){
                const BASE_PATH = 'http';
                let host = window.location.hostname;
                if(window.location.port){
                    host += ':' + window.location.port;
                }
                const proxyURLPrefix = `${BASE_PATH}://${host}`;
                return proxyURLPrefix + proxyUrl;
            },
            
            async loadAllInstances(forceReload){
                this.isLoading = true;
                await Promise.all([this.loadExistingInstances(forceReload), this.loadDeletedInstances(forceReload)]);
                this.isLoading = false;
            },
            
            async loadExistingInstances(forceReload){
                try {
                    if(forceReload || this.existingInstances.length === 0){
                        // workaround: to prevent the instanceButtons from constantly closing.
                        await this.$store.dispatch('loadExistingInstances', forceReload);
                    }
                    if (this.existingInstances.length > 0) {
                        this.loadAllInstanceDetails();
                    }
                }
                catch (e) {
                    this.$eventBus.$emit('showErrorToast', 'Error loading existing instances!');
                }
            },

            async loadDeletedInstances(forceReload) {
                try {
                    await this.$store.dispatch('loadDeletedInstances', forceReload);
                }
                catch (e) {
                    this.$eventBus.$emit('showErrorToast', 'Error loading deleted instances!');
                }
            },

            pollStates() {
                if(this.existingInstancesLoaded) {
                    this.polling = setInterval(() => {
                        this.loadAllInstances(false);
                    }, 5000);
                }
                else {
                    clearInterval(this.polling);
                }
            },

            loadAllInstanceDetails() {
                for (const item of this.existingInstances) {
                    const id = item.instance_id;
                    if(item._showDetails){
                        this.reloadInstanceDetails(id);
                    }
                    else {
                        this.getInstanceState(item);
                    }
                }
            },

            async getInstanceState(item) {
                try {
                    const data = await Server.getInstanceState(item.instance_id);
                    ['status', 'deployment_stuck', 'stuck_duration'].forEach(key => {
                        Vue.set(item, key, data[key]);
                    });
                }
                catch (error) {
                    console.error(error); // eslint-disable-line
                    Vue.set(item, 'status', this.DEFAULT_STATE);
                }
            },
            
            displayInstances() {
                this.existingInstancesLoaded = !this.existingInstancesLoaded;
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