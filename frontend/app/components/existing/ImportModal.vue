<template>
    <b-modal ref="importModalElement" hide-footer title="Import Notebooks" size="lg">
        <loading-spinner v-if="isLoading" class="mt-3"></loading-spinner>
        <table class="table table-striped" v-else-if="storedNotebooks.length > 0">
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Creator</th>
                    <th>Exported</th>
                    <th></th>
                </tr>
            </thead>
            <tbody>
                <tr v-for="(notebook, index) in storedNotebooks" :key="index">
                    <td>{{ notebook.name }}</td>
                    <td>{{ notebook.creator }}</td>
                    <td>{{ formatDate(notebook.created_at) }}</td>
                    <td>
                        <div class="buttonCol">
                            <b-button variant="outline-success" size="sm" @click="doImport(notebook.id)"><fa icon="upload"></fa> Import</b-button>
                            <b-button variant="danger" size="sm" @click="deleteNotebook(notebook.id)"><fa icon="trash-alt"></fa> Delete</b-button>
                        </div>
                    </td>
                </tr>
            </tbody>
        </table>
        <div v-else>
            No notebooks available for import. Please export one first.
        </div>
        <b-btn class="mt-3" variant="outline-danger" block @click="dismiss()">Close</b-btn>
    </b-modal>
</template>

<script>
    import { mapGetters } from 'vuex';
    import Server from '@/server';
    import LoadingSpinner from '@/components/LoadingSpinner';

    export default {
        name: 'ImportModal',
        components: {
            LoadingSpinner
        },
        data() {
            return {
                id: String,
                isLoading: true
            };
        },

        computed: {
            ...mapGetters(['storedNotebooks'])
        },

        methods: {
            open(id) {
                this.id = id;
                this.$refs.importModalElement.show();
                this.loadNotebooks();
            },

            dismiss() {
                this.$refs.importModalElement.hide();
            },
            
            formatDate(s) {
                return new Date(s * 1e3).toLocaleDateString();
            },
            
            async loadNotebooks() {
                try {
                    this.isLoading = true;
                    await this.$store.dispatch('loadStoredNotebooks');
                }
                catch (error) {
                    console.error(error); // eslint-disable-line
                    this.$eventBus.$emit('showErrorToast', 'Error loading stored notebooks!');
                }
                finally {
                    this.isLoading = false;
                }
            },

            async deleteNotebook(notebookId) {
                try {
                    this.isLoading = true;
                    await Server.deleteNotebook(notebookId);
                    await this.$store.dispatch('loadStoredNotebooks');
                    this.$eventBus.$emit('showSuccessToast', `Notebook successfully deleted.`);
                }
                catch (error) {
                    console.error(error); // eslint-disable-line
                    this.$eventBus.$emit('showErrorToast', 'Error deleting notebook');
                }
                finally {
                    this.isLoading = false;
                }
            },
            
            async doImport(notebookId) {
                try {
                    this.isLoading = true;
                    await Server.importNotebook(notebookId, this.id);
                    this.dismiss();
                    this.$eventBus.$emit('showSuccessToast', `Notebook successfully imported.`);
                }
                catch (error) {
                    console.error(error); // eslint-disable-line
                    this.$eventBus.$emit('showErrorToast', 'Error importing notebook');
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