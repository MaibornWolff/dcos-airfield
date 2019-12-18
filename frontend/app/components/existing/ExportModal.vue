<template>
    <div>
        <b-modal ref="exportModalElement" hide-footer title="Export Notebooks">
            <loading-spinner v-if="isLoading" class="mt-3"></loading-spinner>
            <table class="table table-striped" v-else-if="notebooks.length > 0">
                <thead>
                    <tr>
                        <th>Name</th>
                        <th></th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="(notebook, index) in notebooks" :key="index">
                        <td>{{ notebook.name }}</td>
                        <td><b-button variant="outline-success" size="sm" @click="doExport(notebook.id, notebook.name)"><fa icon="download"></fa> Export</b-button></td>
                    </tr>
                </tbody>
            </table>
            <div v-else>
                No notebooks available for export. Please create one on the selected instance.
            </div>
            
            <b-btn class="mt-3" variant="outline-danger" block @click="dismiss()">Close</b-btn>
        </b-modal>
        <b-modal ref="confirmation" ok-variant="danger" @ok="doExport(notebookId, notebookName, true)">
            <loading-spinner v-if="isLoading" class="mt-3"></loading-spinner>
            <template v-else>
                The selected notebook already exists in Airfield. Do you want to overwrite it?
            </template>
        </b-modal>
    </div>
</template>

<script>
    import Server from '@/server';
    import LoadingSpinner from '@/components/LoadingSpinner';

    export default {
        name: 'ExportModal',
        components: {
            LoadingSpinner
        },
        data() {
            return {
                id: String,
                isLoading: true,
                notebooks: Array,
                notebookId: String,
                notebookName: String
            };
        },

        methods: {
            open(id) {
                this.id = id;
                this.$refs.exportModalElement.show();
                this.loadNotebooks();
            },

            dismiss() {
                this.$refs.exportModalElement.hide();
            },

            async loadNotebooks() {
                try {
                    this.isLoading = true;
                    const r = await Server.fetchLocalNotebooks(this.id);
                    this.notebooks = r.notebooks;
                }
                catch (error) {
                    console.error(error); // eslint-disable-line
                    this.$eventBus.$emit('showErrorToast', 'Error loading fetching notebooks from instance!');
                }
                finally {
                    this.isLoading = false;
                }
            },

            async doExport(notebookId, notebookName, force = false) {
                this.notebookId = notebookId;
                this.notebookName = notebookName;
                try {
                    this.isLoading = true;
                    const ret = await Server.exportNotebook(notebookId, notebookName, this.id, force);
                    if (ret === 409) {
                        this.$refs.confirmation.show();
                    }
                    else {
                        this.dismiss();
                        this.$eventBus.$emit('showSuccessToast', `Notebook successfully exported.`);
                    }
                }
                catch (error) {
                    console.error(error); // eslint-disable-line
                    this.$eventBus.$emit('showErrorToast', 'Error exporting notebook');
                }
                finally {
                    this.isLoading = false;
                }
            }

        }
    };
</script>

<style scoped>

</style>