<template>
    <b-container>
        <b-row v-if="isLoading" class="m-3">
            <b-col>
                <loading-spinner></loading-spinner>
            </b-col>
        </b-row>
        
        <b-row v-else class="m-3">
            <template v-if="redeployInstance">
                <b-col sm="12" lg="6" class="secondCol">
                    <b-card>
                        <div slot="header">
                            <fa icon="sliders-h"></fa>
                            <b>Instance Settings</b>
                        </div>

                        <instance-settings v-if="isNewInstanceSelected" class="mt-3"></instance-settings>

                        <div v-else>
                            <fa icon="info-circle"></fa>
                            Selected instance not found
                        </div>
                    </b-card>
                </b-col>
            </template>
            <template v-else>
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
                                v-for="instance in defaultConfigurations" :key="instance.instance_id"
                                :instance="instance"
                            >
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
            </template>
        </b-row>
    </b-container>
</template>


<script>
    import { mapGetters } from 'vuex';

    import InstanceTypeTile from '@/components/configure/InstanceTypeTile';
    import InstanceSettings from '@/components/configure/InstanceSettings';
    import LoadingSpinner from '@/components/LoadingSpinner';
    

    export default {
        components: {
            InstanceSettings, LoadingSpinner, InstanceTypeTile
        },

        data() {
            return {
                isLoading: false,
                instanceId: this.$route.params.instance || '',
                redeployInstance: !!this.$route.params.instance
            };
        },

        computed: {
            ...mapGetters(['defaultConfigurations', 'isNewInstanceSelected'])
        },

        created() {
            this.loadAll();
        },

        destroyed() {
            this.$store.dispatch('resetNewInstance');
        },

        methods: {
            async loadAll(){
                this.isLoading = true;
                await Promise.all([this.loadDcosSettings(), this.loadSelectedInstance(), this.loadDefaultConfigurations(), this.loadInstancePrices()]);
                this.isLoading = false;
            },
            
            async loadSelectedInstance() {
                if (this.redeployInstance) {
                    try {
                        await this.$store.dispatch('loadSelectedInstance', this.instanceId);
                    }
                    catch (error) {
                        console.error(error); // eslint-disable-line
                        this.$eventBus.$emit('showErrorToast', `Error loading instance "${this.instanceId}"!`);
                    }
                }
            },

            async loadDcosSettings(){
                try {
                    await this.$store.dispatch('loadDcosSettings');
                }
                catch (error) {
                    console.error(error); // eslint-disable-line
                }
            },

            async loadInstancePrices(){
                try {
                    await this.$store.dispatch('loadInstancePrices');
                }
                catch (error) {
                    console.error(error); // eslint-disable-line
                }
            },

            async loadDefaultConfigurations(){
                if(!this.redeployInstance) {
                    try {
                        await this.$store.dispatch('loadDefaultConfigurations');
                    }
                    catch (error) {
                        console.error(error); // eslint-disable-line
                        this.$eventBus.$emit('showErrorToast', 'Error loading default configurations!');
                    }
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