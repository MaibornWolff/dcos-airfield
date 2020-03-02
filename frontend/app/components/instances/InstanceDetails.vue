<template>
    <b-card>
        <template v-if="item">
            <b-row class="mt-1">
                <b-col sm="3" class="text-sm-right">
                    <h5>Details</h5>
                </b-col>
            </b-row>
        
            <b-row class="mb-2">
                <b-col sm="3" class="text-sm-right">
                    <b>Created by:</b>
                </b-col>
                <b-col>{{ item.details.created_by }}</b-col>
            </b-row>

            <b-row class="mb-2">
                <b-col sm="3" class="text-sm-right">
                    <b>Created at:</b>
                </b-col>
                <b-col>{{ item.details.created_at }}</b-col>
            </b-row>

            <b-row class="mb-2" v-if="item.details.running_since">
                <b-col sm="3" class="text-sm-right">
                    <b>Running since:</b>
                </b-col>
                <b-col>{{ item.details.running_since }}</b-col>
            </b-row>

            <b-row class="mb-2" v-if="item.details.delete_at">
                <b-col sm="3" class="text-sm-right">
                    <b>Delete at:</b>
                </b-col>
                <b-col>{{ item.details.delete_at }}</b-col>
            </b-row>
            
            <template v-if="item.details.costs">
                <b-row class="mb-2">
                    <b-col sm="3" class="text-sm-right">
                        <b>Running for:</b>
                    </b-col>
                    <b-col>{{ convertTimestamp(item.details.costs.running_time_seconds, 'seconds') }}</b-col>
                </b-row>
                
                <b-row class="mb-2" v-if="costCurrency">
                    <b-col sm="3" class="text-sm-right">
                        <b>The instance costs currently:</b>
                    </b-col>
                    <b-col>{{ item.details.costs.cost.toFixed(2) }} {{ costCurrency }}</b-col>
                </b-row>
            </template>
            
            <template v-if="instanceConfiguration">
                <b-row class="mt-4">
                    <b-col sm="3" class="text-sm-right">
                        <h5>Configuration</h5>
                    </b-col>
                </b-row>
                
                <b-row class="mb-2" v-if="instanceConfiguration.admin.group">
                    <b-col sm="3" class="text-sm-right">
                        <b>Group of the instance:</b>
                    </b-col>
                    <b-col>{{ instanceConfiguration.admin.group }}</b-col>
                </b-row>

                <b-row class="mb-2">
                    <b-col sm="3" class="text-sm-right">
                        <b>Type of the instance:</b>
                    </b-col>
                    <b-col>{{ instanceConfiguration.type }}</b-col>
                </b-row>

                <b-row class="mb-2">
                    <b-col sm="3" class="text-sm-right">
                        <b>Cores of the notebook:</b>
                    </b-col>
                    <b-col>{{ instanceConfiguration.notebook.cores }}</b-col>
                </b-row>

                <b-row class="mb-2">
                    <b-col sm="3" class="text-sm-right">
                        <b>Memory of the notebook:</b>
                    </b-col>
                    <b-col>{{ instanceConfiguration.notebook.memory }}</b-col>
                </b-row>

                <b-row class="mb-2">
                    <b-col sm="3" class="text-sm-right">
                        <b>Maximal cores of spark:</b>
                    </b-col>
                    <b-col>{{ instanceConfiguration.spark.cores_max }}</b-col>
                </b-row>

                <b-row class="mb-2">
                    <b-col sm="3" class="text-sm-right">
                        <b>Cores of spark:</b>
                    </b-col>
                    <b-col>{{ instanceConfiguration.spark.executor_cores }}</b-col>
                </b-row>

                <b-row class="mb-2">
                    <b-col sm="3" class="text-sm-right">
                        <b>Memory of spark:</b>
                    </b-col>
                    <b-col>{{ instanceConfiguration.spark.executor_memory }}</b-col>
                </b-row>
            </template>
        </template>
        <loading-spinner v-if="isLoading" class="mt-3"></loading-spinner>
    </b-card>
</template>

<script>
    import { mapGetters } from 'vuex';

    import LoadingSpinner from '@/components/LoadingSpinner';
    import TimeService from '@/business/timeService';

    export default {
        components: {
            LoadingSpinner
        },

        props: {
            item: {
                type: Object,
                required: true
            },
            existingInstance: {
                type: Boolean,
                required: false,
                default: true
            }
        },
        
        data(){
            return {
                isLoading: false,
                instanceConfiguration: undefined
            };
        },

        computed: {
            ...mapGetters(['dcosSettings', 'costCurrency'])
        },
        
        created() {
            this.loadAll();
        },
        
        methods: {
            convertTimestamp(time){
                return TimeService.humanizeTimestamp(time);
            },
            
            async loadAll(){
                this.isLoading = true;
                await Promise.all([this.loadInstanceConfiguration(), this.loadInstancePrices()]);
                this.isLoading = false;
            },
            
            async loadInstanceConfiguration(){
                if(!this.existingInstance){
                    return;
                }
                const instanceId = this.item.instance_id;
                try{
                    this.instanceConfiguration = await this.$store.dispatch('loadInstanceConfiguration', instanceId);
                }
                catch (e) {
                    this.$eventBus.$emit('showErrorToast', 'Error loading the instance configuration of ' + instanceId + '!');
                }
            },
            
            async loadInstancePrices(){
                try{
                    await this.$store.dispatch('loadInstancePrices');
                }
                catch (e) {
                    console.error(e);
                }
            }
        }


    };
</script>
