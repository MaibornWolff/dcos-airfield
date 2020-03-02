<template>
    <div>
        <b-card no-body>
            <b-tabs pills card justified>
                <b-tab title="General" active>
                    <label>Comment</label>
                    <b-form-input v-model="selectedNewInstance.comment" placeholder="Comment"></b-form-input>

                    <label>Delete instance at</label>
                    <b-form-input v-model="selectedNewInstance.delete_at" type="date"></b-form-input>

                    <b-container class="mt-4">
                        <b-row class="alignedRow">
                            <b-col>
                                <b-input-group append="# CPUs">
                                    <b-form-input v-model="selectedNewInstance.notebook.cores" type="number"></b-form-input>
                                </b-input-group>
                            </b-col>
                            <b-col>
                                <b-input-group append="RAM (MB)">
                                    <b-form-input v-model="selectedNewInstance.notebook.memory" type="number"></b-form-input>
                                </b-input-group>
                            </b-col>
                        </b-row>
                    </b-container>
                </b-tab>

                <b-tab title="Spark">
                    <b-container class="mt-4">
                        <b-row class="alignedRow">
                            <b-col>
                                <b-input-group append="# Executor cores" class="config-group">
                                    <b-form-input v-model="selectedNewInstance.spark.executor_cores" type="number"></b-form-input>
                                </b-input-group>
                            </b-col>
                        </b-row>
                        <b-row class="alignedRow">
                            <b-col>
                                <b-input-group append="# Max cores" class="config-group">
                                    <b-form-input v-model="selectedNewInstance.spark.cores_max" type="number"></b-form-input>
                                </b-input-group>
                            </b-col>
                        </b-row>
                        <b-row class="alignedRow">
                            <b-col>
                                <b-input-group append="Executor RAM (MB)" class="config-group">
                                    <b-form-input v-model="selectedNewInstance.spark.executor_memory" type="number"></b-form-input>
                                </b-input-group>
                            </b-col>
                        </b-row>
                    </b-container>

                    <label>Pyspark Python</label>
                    <b-form-input v-model="selectedNewInstance.spark.python_version"></b-form-input>
                </b-tab>

                <b-tab title="Libraries">
                    <h6><fa :icon="['fab', 'python']"></fa> Additional Python Libraries</h6>
                    <label class="mt-0">Custom libraries (separate with ";")</label>
                    <b-form-input v-model="additionalPythonLibraries"></b-form-input>
                
                    <h6><fa icon="registered"></fa> Additional R Libraries</h6>
                    <label class="mt-0">Custom libraries (separate with ";")</label>
                    <b-form-input v-model="additionalRLibraries"></b-form-input>
                </b-tab>

                <b-tab title="Costs" v-if="costTrackingEnabled">
                    <h6><fa icon="microchip"></fa>CPU Core</h6>
                    <label>One CPU costs {{ (costCorePerMinute * 60).toFixed(2) }} {{ costCurrency }} per hour.</label>

                    <h6><fa icon="hdd"></fa>RAM</h6>
                    <label>One GB RAM costs {{ (costGBPerMinute * 60).toFixed(2) }} {{ costCurrency }} per hour.</label>
                
                    <h6><fa icon="money-bill-alt"></fa>Costs</h6>
                    <template v-if="!costsLoading">
                        <label v-if="costsUpToDate">Using this configuration the instance costs {{ instanceCosts.toFixed(2) }} {{ costCurrency }} per hour.</label>
                        <b-button v-if="!costsUpToDate" size="sm" variant="info" class="btn" @click="calculateCosts">
                            Calculate costs
                        </b-button>
                    </template>
                    <loading-spinner v-if="costsLoading"></loading-spinner>
                </b-tab>

                <b-tab title="User management">
                    <b-container>
                        <b-row class="mt-2">
                            <h6>Options</h6>
                        </b-row>
                        <b-row class="mt-2">
                            <b-col>
                                <b-form-checkbox v-model="selectedNewInstance.usermanagement.enabled">
                                    User management enabled
                                </b-form-checkbox>
                            </b-col>
                        </b-row>
                    </b-container>
                    <b-container v-if="selectedNewInstance.usermanagement.enabled">
                        <b-row class="mt-4">
                            <h6>Users</h6>
                        </b-row>
                        <b-row v-for="(username, index) in Object.keys(selectedNewInstance.usermanagement.users)" :key="index" class="text-center">
                            <b-col>
                                <span>
                                    {{ username }}
                                </span>
                            </b-col>
                            <b-col>
                                <span>
                                    {{ selectedNewInstance.usermanagement.users[username] }}<!-- password -->
                                </span>
                            </b-col>
                            <b-col>
                                <fa @click="deleteRow(username)" icon="trash-alt" class="deleteBtn"></fa>
                            </b-col>
                        </b-row>
                        <b-row class="text-center">
                            <b-col>
                                <b-form-input v-model="newUsername" placeholder="username"></b-form-input>
                            </b-col>
                            <b-col>
                                <b-form-input v-model="newPassword" placeholder="password"></b-form-input>
                            </b-col>
                            <b-col>
                                <b-button size="sm" variant="outline-info" class="btn" @click="addUser">
                                    Add new user
                                </b-button>
                            </b-col>
                        </b-row>
                    </b-container>
                </b-tab>

                <b-tab title="Administration" v-if="oidcActivated" ref="administrationTab">
                    <b-container class="mt-4" v-if="areGroupsSelectable">
                        <h6>Group</h6>
                        <div>
                            <b-form-select v-model="selectedNewInstance.admin.group" :options="dcosGroups" class="mb-3">
                                <template v-slot:first>
                                    <option :value="null" disabled>
                                        -- Please select a group --
                                    </option>
                                </template>
                            </b-form-select>
                        </div>
                    </b-container>
                    <b-container class="mt-4">
                        <h6>Admins</h6>
                        <label class="mt-0">List of admins (separate with ";")</label>
                        <b-form-input v-model="admins"></b-form-input>
                    </b-container>
                </b-tab>
            </b-tabs>
        </b-card>
        <br>
        <create-instance-button
            @select-administration-tab="selectAdministrationTab"
        ></create-instance-button>
    </div>
</template>


<script>
    import Vue from 'vue';
    import { mapGetters } from 'vuex';

    import CreateInstanceButton from '@/components/configure/CreateInstanceButton';
    import LoadingSpinner from '@/components/LoadingSpinner';
    import Server from '@/server/instance';
    
    function cleanString(str, substr = ' '){
        return str.replace(new RegExp(substr, 'g'), '');
    }
    
    function accessor(key1, key2){
        return {
            get() {
                const item = this.selectedNewInstance[key1][key2];
                return item ? item.join(';') : '';
            },
            set(value) {
                if (this.selectedNewInstance[key1] !== undefined) {
                    Vue.set(this.selectedNewInstance[key1], key2, cleanString(value).split(';'));
                }
            }
        };
    }

    export default {
        components: {
            CreateInstanceButton, LoadingSpinner
        },
        
        data() {
            return {
                newUsername: '',
                newPassword: '',
                costsUpToDate: false,
                instanceCosts: 0.0,
                costsLoading: false,
                areGroupsSelectable: false,
                isAdministrationActive: false
            };
        },

        computed: {
            ...mapGetters(['selectedNewInstance',
                'isSelectedInstanceExisting',
                'selectedNewInstanceId',
                'dcosGroups',
                'oidcActivated',
                'dcosGroupsActivated',
                'costCurrency',
                'costTrackingEnabled',
                'costCorePerMinute',
                'costGBPerMinute',
                'username']),
            
            additionalPythonLibraries: accessor('libraries', 'python'),
            additionalRLibraries: accessor('libraries', 'r'),
            admins: accessor('admin', 'admins')
        },

        watch: {
            selectedNewInstance: {
                deep: true,
                immediate: true,
                handler: function() {
                    this.costsUpToDate = false;
                }
            }
        },
        
        created() {
            this.areGroupsSelectable = !this.isSelectedInstanceExisting && this.oidcActivated && this.dcosGroupsActivated;
            if(this.areGroupsSelectable && this.dcosGroups.length === 0){
                this.$eventBus.$emit('showErrorToast', `There are no groups available for the user ${this.username}! \n Please add one to your Keycloak account or the available groups of Airfield!`);
            }
        },

        methods: {
            selectAdministrationTab(){
                this.$refs.administrationTab.activate();
            },
            
            addUser() {
                if(this.newUsername !== ''){
                    Vue.set(this.selectedNewInstance.usermanagement.users, this.newUsername, this.newPassword);
                    this.newUsername = '';
                    this.newPassword = '';
                }
            },
            
            deleteRow(username) {
                Vue.delete(this.selectedNewInstance.usermanagement.users, username);
            },
            
            async calculateCosts(){
                this.costsLoading = true;
                try{
                    Vue.set(this, 'instanceCosts', await Server.calculateCosts(this.selectedNewInstance));
                    this.costsUpToDate = true;
                }
                catch (e) {
                    this.$eventBus.$emit('showErrorToast', `Error calculating the costs!`);
                }
                finally {
                    this.costsLoading = false;
                }
            }
        }
    };
</script>


<style lang="scss" scoped>
    @import "~@/assets/styles/variables";

    label {
        margin-top: 1rem;
        margin-bottom: 0;
        font-size: 0.8rem;
        font-weight: bold;
    }

    .alignedRow {
        margin: 0 -30px;
        .config-group {
            margin: 5px
        }
    }

    h6 {
        margin: 20px 0 10px;
        font-weight: bold;
    }
    
    .deleteBtn {
        margin-top: 0.6rem;
        cursor: pointer;
        color: $delete-btn-color;
    }
    
</style>