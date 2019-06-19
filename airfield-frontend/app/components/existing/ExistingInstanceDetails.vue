<template>
    <b-card v-if="item.status !== 'NOT_FOUND'">
        <b-row class="mb-2">
            <b-col sm="3" class="text-sm-right"><b>Created by:</b></b-col>
            <b-col>{{ item.createdBy }}</b-col>
        </b-row>

        <b-row class="mb-2">
            <b-col sm="3" class="text-sm-right"><b>Created at:</b></b-col>
            <b-col>{{ toUTCString(item.created_at) }}</b-col>
        </b-row>
        
        <template v-if="typeof item.deleted_at === 'undefined'">
            <b-row class="mb-2" v-if="status === 'RUNNING'">
                <b-col sm="3" class="text-sm-right"><b>Running since:</b></b-col>
                <b-col>{{ toUTCString(time) }}</b-col>
            </b-row>
        
            <b-row class="mb-2" v-if="status === 'STOPPED'">
                <b-col sm="3" class="text-sm-right"><b>Stopped since:</b></b-col>
                <b-col>{{ toUTCString(time) }}</b-col>
            </b-row>
        </template>
        
        <b-row class="mb-2" v-if="typeof runningTimeHumanized !== 'undefined'">
            <b-col sm="3" class="text-sm-right"><b>Complete Running Time:</b></b-col>
            <b-col>{{ runningTimeHumanized }}</b-col>
        </b-row>

        <b-row class="mb-2" v-if="typeof costsHumanized !== 'undefined'">
            <b-col sm="3" class="text-sm-right"><b>Complete Costs:</b></b-col>
            <b-col>{{ costsHumanized }}</b-col>
        </b-row>

        <b-row class="mb-2">
            <b-col sm="3" class="text-sm-right"><b>Number of CPU cores:</b></b-col>
            <b-col>{{ getNumberOfCPUCores(item.configuration) }}</b-col>
        </b-row>

        <b-row class="mb-2">
            <b-col sm="3" class="text-sm-right"><b>Number of RAM in GB:</b></b-col>
            <b-col>{{ getNumberOfRAM(item.configuration) }}</b-col>
        </b-row>
    </b-card>
</template>

<script>
    import TimeService from '@/business/timeService';
    
    export default {
        name: 'ExistingInstanceDetails',
        
        props: {
            item: {
                type: Object,
                required: true
            }
        },
        
        data() {
            return {
                status: 'NOT_FOUND',
                time: 0,
                pollingRunningTime: undefined,
                runningTimeAsTimeStamp: 0,
                runningTimeHumanized: undefined,
                pollingCosts: undefined,
                costsHumanized: undefined
            };
        },
        
        created() {
            this.status = this.item.history[this.item.history.length - 1].status;
            this.time = this.item.history[this.item.history.length - 1].time;
            this.runningTimeAsTimeStamp = this.sumRunningTime();
            this.setRunningTime();
            this.setCosts();
        },
        
        beforeDestroy() {
            clearInterval(this.pollingRunningTime);
            clearInterval(this.pollingCosts);
        },
        
        methods: {
            toUTCString(time){
                return TimeService.toUTCString(time);
            },
            
            formatCosts(costObject) {
                if (typeof costObject === 'undefined') {
                    return costObject;
                }
                let actualCost = '';
                actualCost += costObject.EURO > 0 ? costObject.EURO.toFixed(2) + ' EURO; ' : '';
                actualCost += costObject.POUND > 0 ? costObject.POUND.toFixed(2) + ' POUND; ' : '';
                actualCost += costObject.DOLLAR > 0 ? costObject.DOLLAR.toFixed(2) + ' DOLLAR; ' : '';
                if (actualCost === '') {
                    actualCost = '0.00 ' + this.item.configuration.costsAsObject.currency + '; ';
                }
                return actualCost;
            },

            sumCosts(statusList) {
                if (typeof statusList === 'undefined') {
                    statusList = ['RUNNING', 'STOPPED'];
                }
                if (typeof statusList === 'string') {
                    statusList = [statusList];
                }
                const costs = {
                    EURO: 0,
                    POUND: 0,
                    DOLLAR: 0
                };
                const historyLength = this.item.history.length - 1;
                for (let i = 0; i < historyLength; i++) {
                    if (statusList.includes(this.item.history[i].status)) {
                        costs[this.item.history[i].costsAsObject.currency] += this.computeCosts(i);
                    }
                }
                if (typeof this.item.deleted_at !== 'undefined') {
                    costs[this.item.history[historyLength].costsAsObject.currency] += this.computeCosts(historyLength, this.item.deleted_at - this.time);
                }
                else {
                    costs[this.item.history[historyLength].costsAsObject.currency] += this.computeCosts(historyLength, new Date().getTime() / 1000 - this.time);
                }
                return costs;
            },

            computeCosts(index, time) {
                if (typeof time === 'undefined') {
                    if (index >= this.item.history.length) {
                        console.error('The index: ' + index + 'has to be smaller or equals then ' + (this.item.history.length - 1) + '.');
                        return 0;
                    }
                    time = this.item.history[index + 1].time - this.item.history[index].time;
                }
                const coreCost = this.item.history[index].costsAsObject.core_per_minute * (parseInt(this.item.history[index].resources.spark.cpu_cores, 10) * parseInt(this.item.configuration.instances, 10) + parseInt(this.item.history[index].resources.zeppelin.cpu_cores, 10));
                const ramCost = this.item.history[index].costsAsObject.core_per_minute * (parseFloat(this.item.history[index].resources.spark.ram) * 1024 * parseInt(this.item.configuration.instances, 10) + parseFloat(this.item.history[index].resources.zeppelin.ram)) / 1000;
                return (coreCost + ramCost) * (time / 60);

            },

            setCosts() {
                if (!this.pollingCosts) {
                    this.costsHumanized = this.formatCosts(this.sumCosts());
                    if (typeof this.item.deleted_at === 'undefined') {
                        this.pollingCosts = setInterval(() => {
                            this.costsHumanized = this.formatCosts(this.sumCosts());
                        }, 30000);
                    }
                }
            },

            setRunningTime() {
                if (typeof this.item.deleted_at !== 'undefined') {
                    clearInterval(this.pollingRunningTime);
                    this.runningTimeHumanized = TimeService.formatRunningTime(this.runningTimeAsTimeStamp + this.item.deleted_at - this.time);
                }
                else if (this.status === 'STOPPED') {
                    clearInterval(this.pollingRunningTime);
                    this.runningTimeHumanized = TimeService.formatRunningTime(this.runningTimeAsTimeStamp);
                }
                else if (this.status === 'RUNNING') {
                    if (!this.pollingRunningTime) {
                        this.runningTimeHumanized = TimeService.formatRunningTime(this.runningTimeAsTimeStamp + (Date.now() / 1000) - this.time);
                        this.pollingRunningTime = setInterval(() => {
                            this.runningTimeHumanized = TimeService.formatRunningTime(this.runningTimeAsTimeStamp + (Date.now() / 1000) - this.time);
                        }, 1000);
                    }
                }
                else {
                    clearInterval(this.pollingRunningTime);
                    this.runningTimeHumanized = undefined;
                }
            },

            sumRunningTime() {
                let sum = 0;
                for (let i = 0; i <= this.item.history.length - 2; i++) {
                    if (this.item.history[i].status === 'RUNNING') {
                        sum += this.item.history[i + 1].time - this.item.history[i].time;
                    }
                }
                return sum;
            },
            getNumberOfCPUCores(configuration) {
                return +configuration.cpus + +configuration.env.SPARK_CORES_MAX * +configuration.instances;
            },

            getNumberOfRAM(configuration) {
                return (+configuration.mem + 1024 * parseFloat(configuration.env.SPARK_EXECUTOR_MEMORY) * +configuration.instances) / 1000;
            }
        }
    };
</script>

<style scoped>

</style>