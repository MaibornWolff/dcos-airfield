<template>
    <b-container>
        <b-row v-if="isLoading" class="m-3">
            <b-col>
                <loading-spinner></loading-spinner>
            </b-col>
        </b-row>
        
        <b-row class="m-3">
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
            this.propagateInstanceData();
        },

        destroyed() {
            this.$store.dispatch('resetNewInstance');
        },

        methods: {
            async propagateInstanceData() {
                if (this.$route.params.instance !== '') {
                    try {
                        this.isLoading = true;
                        await this.$store.dispatch('findInstance', this.$route.params.instance);
                    }
                    catch (error) {
                        console.error(error); // eslint-disable-line
                        this.$eventBus.$emit('showErrorToast', 'Error loading instance!');
                    }
                    finally {
                        this.isLoading = false;
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

    @media (max-width: 991px) {
        .secondCol {
            margin-top: 25px;
        }
    }
</style>