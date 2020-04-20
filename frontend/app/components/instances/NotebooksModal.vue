<template>
    <div>
        <b-modal size="xl" ref="notebookModalElement" title="Notebook administration" scrollable ok-title="close" ok-only ok-variant="outline-danger">
            <b-card class="m-3">
                <div slot="header" class="cardHeader">
                    <div class="cardTitle">
                        <fa icon="list"></fa>
                        <b>
                            {{ isImport ? 'Notebooks for import' : 'Notebooks for export' }}
                            <fa icon="spinner" spin v-if="isLoading || actionInProgress"></fa>
                        </b>
                    </div>
                    <div v-if="!isLoading">
                        <template v-if="!isImport">
                            <b-button v-for="action in actions"
                                      :key="action.key"
                                      size="sm"
                                      class="m-1"
                                      :variant="action.variant"
                                      @click="triggerAction(action)"
                                      :disabled="actionInProgress"
                            >
                                <fa :icon="action.icon"></fa>
                                {{ action.name }}
                            </b-button>
                        </template>
                        <b-button class="m-1" size="sm" @click="switchImportExport()">
                            <fa icon="list"></fa>
                            {{ isImport ? 'Show notebooks for export' : 'Show notebooks for import' }}
                        </b-button>
                        <b-button class="m-1" size="sm" @click="resetAndReload()">
                            <fa icon="sync"></fa> Refresh
                        </b-button>
                    </div>
                </div>
                <template class="card-body">
                    <loading-spinner v-if="isLoading" class="mt-3"></loading-spinner>
                    <template v-else>
                        <template v-if="!isImport">
                            <b-table v-if="notebooks.length > 0" striped hover :items="notebooks" :fields="fields" class="mt-4">
                                <template v-slot:cell(buttons)="row">
                                    <b-button class="m-1" variant="outline-success" size="sm" @click="doExport(row.item.id, row.item.name)">
                                        <fa icon="upload"></fa> Export
                                    </b-button>
                                    <b-button class="m-1" variant="danger" size="sm" @click="triggerAction({ key: 'delete' }, row.item.id)">
                                        <fa icon="trash-alt"></fa> Delete
                                    </b-button>
                                </template>
                            </b-table>
                            <div v-else>
                                No notebooks available on the selected instance. Please create one.
                            </div>
                        </template>
                        <template v-if="isImport">
                            <b-table v-if="storedNotebooks.length > 0" striped hover :items="storedNotebooks" :fields="fields" class="mt-4">
                                <template v-slot:cell(buttons)="row">
                                    <b-button class="m-1" variant="outline-success" size="sm" @click="triggerAction({ key: 'import' }, row.item.id)">
                                        <fa icon="upload"></fa> Import
                                    </b-button>
                                </template>
                            </b-table>
                            <div v-else>
                                No notebook available at all. Please create one for any instance.
                            </div>
                        </template>
                    </template>
                </template>
            </b-card>
        </b-modal>
        <confirmation-modal
            ref="confirmation"
            @ok="doExport(notebookId, notebookName, true)"
            ok-title="Overwrite"
            message="The selected notebook already exists in Airfield. Do you want to overwrite it?"
        >
        </confirmation-modal>
    </div>
</template>

<script>
    import { mapGetters } from 'vuex';

    import Server from '@/server/notebook';
    import LoadingSpinner from '@/components/LoadingSpinner';
    import ConfirmationModal from '@/components/ConfirmationModal';
    
    export default {
        name: 'NotebooksModal',
        
        components: {
            LoadingSpinner, ConfirmationModal
        },

        data() {
            return {
                instanceId: String,
                isLoading: false,
                actionInProgress: false,
                notebookId: String,
                notebookName: String,
                notebooks: Array,
                isImport: false,
                fields: [
                    { key: 'name', label: 'Name', sortable: true },
                    { key: 'buttons', label: '' }
                ],
                actions: [
                    { key: 'backupNotebooks', name: 'Backup notebooks', variant: 'outline-primary', icon: 'save' },
                    { key: 'restoreNotebooks', name: 'Restore notebooks', variant: 'outline-success', icon: 'window-restore' },
                    { key: 'cancelRestoreNotebooks', name: 'Cancel restore notebooks', variant: 'outline-warning', icon: 'ban' }
                ]
            };
        },

        computed: {
            ...mapGetters(['instanceNotebooks', 'storedNotebooks'])
        },

        methods: {
            resetAndReload(){
                this.loadAll(true);
            },
            
            switchImportExport(){
                this.isImport = !this.isImport;
            },
            
            open(id, forceReload) {
                this.instanceId = id;
                this.$refs.notebookModalElement.show();
                this.loadAll(forceReload);
            },
            
            async loadAll(forceReload = false){
                this.isLoading = true;
                await Promise.all([this.loadStoredNotebooks(forceReload), this.loadInstanceNotebooks(forceReload)]);
                this.isLoading = false;
            },

            dismiss() {
                this.$refs.notebookModalElement.hide();
            },

            async loadInstanceNotebooks(forceReload) {
                try {
                    await this.$store.dispatch('loadInstanceNotebooks', { instanceId: this.instanceId, forceReload: forceReload });
                    this.notebooks = this.instanceNotebooks[this.instanceId];
                }
                catch (error) {
                    console.error(error);
                    this.$eventBus.$emit('showErrorToast', 'Error fetching notebooks from instance!');
                }
            },

            async loadStoredNotebooks(forceReload) {
                try {
                    await this.$store.dispatch('loadStoredNotebooks', forceReload);
                }
                catch (error) {
                    console.error(error); // eslint-disable-line
                    this.$eventBus.$emit('showErrorToast', 'Error loading stored notebook!');
                }
            },

            async doExport(notebookId, notebookName, force = false) {
                this.notebookId = notebookId;
                this.notebookName = notebookName;
                this.actionInProgress = true;
                try {
                    const ret = await Server.exportNotebook(notebookId, this.instanceId, force);
                    if (ret === 409) {
                        this.$refs.confirmation.show();
                    }
                    else {
                        this.$eventBus.$emit('showSuccessToast', `Notebook successfully exported.`);
                        this.resetAndReload();
                    }
                }
                catch (error) {
                    console.error(error); // eslint-disable-line
                    this.$eventBus.$emit('showErrorToast', 'Error exporting notebook');
                }
                finally {
                    this.actionInProgress = false;
                }
            },
            
            async triggerAction(action, notebookId){
                const payload = { instanceId: this.instanceId, notebookId: notebookId };
                let successMessage, errorMessage = `Could not trigger action ${action.name || action.key || action}!`, serverFunction;
                switch (action.key) {
                    case 'import':
                        successMessage = `Notebook successfully imported.`;
                        errorMessage = 'Error importing notebook';
                        serverFunction = Server.importNotebook;
                        break;
                    case 'delete':
                        successMessage = `Notebook successfully deleted.`;
                        errorMessage = 'Error deleting notebook';
                        serverFunction = Server.deleteNotebook;
                        break;
                    case 'backupNotebooks':
                        successMessage = `Notebooks successfully backed up.`;
                        errorMessage = 'Error backing up notebooks';
                        serverFunction = Server.backupNotebooks;
                        break;
                    case 'restoreNotebooks':
                        successMessage = `Notebook successfully restored.`;
                        errorMessage = 'Error restoring notebook';
                        serverFunction = Server.restoreNotebooks;
                        break;
                    case 'cancelRestoreNotebooks':
                        successMessage = `Restoring notebooks successfully canceled.`;
                        errorMessage = 'Error canceling restoring notebooks';
                        serverFunction = Server.cancelRestoreNotebooks;
                        break;
                    default:
                        this.$eventBus.$emit('showErrorToast', errorMessage);
                        return;
                }
                this.actionInProgress = true;
                try {
                    await serverFunction(payload);
                    this.$eventBus.$emit('showSuccessToast', successMessage);
                    this.resetAndReload();
                }
                catch (error) {
                    console.error(error); // eslint-disable-line
                    this.$eventBus.$emit('showErrorToast', errorMessage);
                }
                finally {
                    this.actionInProgress = false;
                }
            }
        }
    };
</script>

<style scoped>
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