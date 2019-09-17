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
            <b-col>{{ getNumberOfCPUCores() }}</b-col>
        </b-row>

        <b-row class="mb-2">
            <b-col sm="3" class="text-sm-right"><b>Number of RAM in GB:</b></b-col>
            <b-col>{{ getNumberOfRAM() }}</b-col>
        </b-row>
    </b-card>
</template>

<script>
    import TimeService from '@/business/timeService';
    import CostService from '@/business/costService';
    
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
                return costObject[this.item.configuration.costsAsObject.currency].toFixed(2) + ' ' + this.item.configuration.costsAsObject.currency + '; ';
            },

            sumCosts(statusList) {
                if (typeof statusList === 'undefined') {
                    statusList = ['RUNNING', 'STOPPED'];
                }
                if (typeof statusList === 'string') {
                    statusList = [statusList];
                }
                const costs = {};
                costs[this.item.configuration.costsAsObject.currency] = 0;
                const historyLength = this.item.history.length - 1;
                for (let i = 0; i < historyLength; i++) {
                    if (statusList.includes(this.item.history[i].status)) {
                        costs[this.item.configuration.costsAsObject.currency] += this.computeCosts(i);
                    }
                }
                if (typeof this.item.deleted_at !== 'undefined') {
                    costs[this.item.configuration.costsAsObject.currency] += this.computeCosts(historyLength, this.item.deleted_at - this.time);
                }
                else {
                    costs[this.item.configuration.costsAsObject.currency] += this.computeCosts(historyLength, new Date().getTime() / 1000 - this.time);
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
                const corePerMinute = this.item.configuration.costsAsObject.core_per_minute;
                const ramPerMinute = this.item.configuration.costsAsObject.ram_in_gb_per_minute;
                const sparkCpus = parseInt(this.item.history[index].resources.spark.cpus, 10);
                const zeppelinCpus = parseInt(this.item.history[index].resources.zeppelin.cpus, 10);
                const sparkMemInMB = parseFloat(this.item.history[index].resources.spark.mem);
                const zeppelinMemInGB = parseFloat(this.item.history[index].resources.zeppelin.mem);
                const instances = parseInt(this.item.configuration.instances, 10);
                
                const coreCost = corePerMinute * (sparkCpus * instances + zeppelinCpus);
                const ramCost = ramPerMinute * (sparkMemInMB * 1024 * instances + zeppelinMemInGB) / 1000;
                const roundedTime = Math.floor(time);
                
                return (coreCost + ramCost) * (roundedTime / 60);

            },

            setCosts() {
                this.costsHumanized = this.formatCosts(this.sumCosts());
                if (typeof this.item.deleted_at === 'undefined') {
                    this.pollingCosts = setInterval(() => {
                        this.costsHumanized = this.formatCosts(this.sumCosts());
                    }, 500);
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
            getNumberOfCPUCores() {
                return CostService.getNumberOfCPUCores(this.item.configuration);
            },

            getNumberOfRAM() {
                return CostService.getNumberOfRAM(this.item.configuration);
            }
        }
    };
</script>

<style scoped>

</style>