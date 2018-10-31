<template>
    <b-container>
        <b-row v-if="isLoading" class="m-3">
            <b-col>
                <loading-spinner></loading-spinner>
            </b-col>
        </b-row>

        <div v-else-if="defaultConfigurations.length === 0" class="noDataText mt-3">No options available.</div>

        <b-row v-else class="m-3">
            <b-col sm="12" lg="6">
                <b-card>
                    <div slot="header">
                        <fa icon="box"></fa>
                        <b>Instance Types</b>
                    </div>

                    <div class="mb-3">
                        Select an instance type you want to create.
                    </div>

                    <div class="instanceTypeTiles">
                        <instance-type-tile
                            v-for="instance in defaultConfigurations" :key="instance.id"
                            :instance="instance">
                        </instance-type-tile>
                    </div>
                </b-card>
            </b-col>

            <b-col sm="12" lg="6" class="secondCol">
                <b-card>
                    <div slot="header">
                        <fa icon="sliders-h"></fa>
                        <b>Instance Settings</b>
                    </div>

                    <instance-settings v-if="isNewInstanceSelected" class="mt-3"></instance-settings>

                    <div v-else>
                        <fa icon="info-circle"></fa>
                        Select an instance type.
                    </div>
                </b-card>
            </b-col>
        </b-row>
    </b-container>
</template>


<script>
    import { mapGetters } from 'vuex';

    import InstanceTypeTile from '@/components/add/InstanceTypeTile';
    import InstanceSettings from '@/components/add/InstanceSettings';
    import LoadingSpinner from '@/components/LoadingSpinner';

    export default {
        components: {
            InstanceTypeTile, InstanceSettings, LoadingSpinner
        },

        data() {
            return {
                isLoading: false
            };
        },

        computed: {
            ...mapGetters(['defaultConfigurations', 'isNewInstanceSelected'])
        },
        
        created() {
            this.loadDefaultConfigurations();
        },

        destroyed() {
            this.$store.dispatch('resetNewInstance');
        },

        methods: {
            async loadDefaultConfigurations() {
                try {
                    this.isLoading = true;
                    await this.$store.dispatch('loadDefaultConfigurations');
                }
                catch (error) {
                    console.error(error); // eslint-disable-line
                    this.$eventBus.$emit('showErrorToast', 'Error loading default configurations!');
                }
                finally {
                    this.isLoading = false;
                }
            }
        }
    };
</script>


<style lang="scss" scoped>
    .card-header svg {
        margin-right: 7px;
    }

    .noDataText {
        font-weight: bold;
        text-align: center;
    }
    
    .instanceTypeTiles {
        display: flex;
        flex-wrap: wrap;

        > div {
            flex: 1;
        }
    }

    @media (max-width: 991px) {
        .secondCol {
            margin-top: 25px;
        }
    }
</style>