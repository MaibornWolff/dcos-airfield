<template>
    <div>
        <b-tabs>
            <b-tab title="General" active>
                <label>Comment</label>
                <b-form-input v-model="selectedNewInstance.comment" placeholder="Comment"></b-form-input>

                <label>Delete instance at</label>
                <b-form-input v-model="selectedNewInstance.deleteAt" type="date"></b-form-input>

                <b-container class="mt-4">
                    <b-row class="alignedRow">
                        <b-col>
                            <b-input-group append="# CPUs">
                                <b-form-input v-model="selectedNewInstance.configuration.cpus" type="number"></b-form-input>
                            </b-input-group>
                        </b-col>
                        <b-col>
                            <b-input-group append="RAM (MB)">
                                <b-form-input v-model="selectedNewInstance.configuration.mem" type="number"></b-form-input>
                            </b-input-group>
                        </b-col>
                    </b-row>
                </b-container>
            </b-tab>

            <b-tab title="Spark">
                <b-container class="mt-4">
                    <b-row class="alignedRow">
                        <b-col>
                            <b-input-group append="Max cores">
                                <b-form-input v-model="selectedNewInstance.configuration.env.SPARK_CORES_MAX" type="number"></b-form-input>
                            </b-input-group>
                        </b-col>
                        <b-col>
                            <b-input-group append="RAM">
                                <b-form-input v-model="selectedNewInstance.configuration.env.SPARK_EXECUTOR_MEMORY"></b-form-input>
                            </b-input-group>
                        </b-col>
                    </b-row>
                </b-container>

                <label>Pyspark Python</label>
                <b-form-input v-model="selectedNewInstance.configuration.env.PYSPARK_PYTHON"></b-form-input>
            </b-tab>

            <b-tab title="Libraries">
                <h6><fa :icon="['fab', 'python']"></fa> Additional Python Libraries</h6>
                <b-form-checkbox v-model="selectedNewInstance.configuration.libraries[0].tensorflow">
                    Tensorflow
                </b-form-checkbox>
                <br>
                
                <label>Custom libraries (separate with ";")</label>
                <b-form-input v-model="additionalPythonLibraries"></b-form-input>
                
                <h6><fa icon="registered"></fa> Additional R Libraries</h6>
                <label class="mt-0">Custom libraries (separate with ";")</label>
                <b-form-input v-model="additionalRLibraries"></b-form-input>
            </b-tab>

            <b-tab title="Costs">
                <h6><fa icon="microchip"></fa>CPU Core</h6>
                <label>One CPU costs {{ (selectedNewInstance.configuration.costsAsObject.core_per_minute * 60).toFixed(2) }} {{ selectedNewInstance.configuration.costsAsObject.currency }} per hour.</label>

                <h6><fa icon="hdd"></fa>RAM</h6>
                <label>One GB RAM costs {{ (selectedNewInstance.configuration.costsAsObject.core_per_minute * 60).toFixed(2) }} {{ selectedNewInstance.configuration.costsAsObject.currency }} per hour.</label>
                
                <h6><fa icon="money-bill-alt"></fa>Costs</h6>
                <label>Using this configuration the instance costs {{ getInstanceCostsPerHour().toFixed(2) }} {{ selectedNewInstance.configuration.costsAsObject.currency }} per hour.</label>
                <br>
            </b-tab>

            <b-tab title="Security">
                <b-container class="mt-4">
                    <b-row>
                        <b-form-group label="Generate users/passwords on startup">
                            <b-form-radio-group buttons
                                                v-model="selectedNewInstance.configuration.usermanagement"
                                                :options="options"
                                                name="usermanagement"
                            ></b-form-radio-group>
                        </b-form-group>
                    </b-row>
                </b-container>
                <b-container v-if="selectedNewInstance.configuration.usermanagement !== 'no' ">
                    <b-row v-for="(user, index) in selectedNewInstance.configuration.users" :key="index" class="mt-1 alignedRow">
                        <b-col>
                            <b-form-input v-model="user.username" placeholder="Username"></b-form-input>
                        </b-col>
                        <b-col v-if="selectedNewInstance.configuration.usermanagement === 'manual'">
                            <b-form-input v-model="user.password" placeholder="Password"></b-form-input>
                        </b-col>
                        <b-col>
                            <fa @click="deleteRow(user)" icon="trash-alt" class="deleteBtn"></fa>
                        </b-col>
                    </b-row>
                    <b-row class="alignedRow mt-2" v-if="checkShowAdd">
                        <b-col>
                            <button class="btn" @click="addRow()">
                                Add new user
                            </button>
                        </b-col>
                    </b-row>
                </b-container>
            </b-tab>
        </b-tabs>

        <br>
        <create-instance-button></create-instance-button>
    </div>
</template>


<script>
    import { mapGetters } from 'vuex';

    import CreateInstanceButton from '@/components/add/CreateInstanceButton';
    import CostService from '@/business/costService';

    function libraryAccessor(language) {
        const findLibrary = instance => instance.configuration.libraries.find(e => e.language === language);
        return {
            get() {
                const item = findLibrary(this.selectedNewInstance);
                return item ? item.libraries.join(';') : '';
            },
            set(value) {
                const item = findLibrary(this.selectedNewInstance);
                if (item) {
                    item.libraries = value.split(';');
                }
            }
        };
    }

    export default {
        components: {
            CreateInstanceButton
        },
        data() {
            return {
                options: [
                    { text: 'No Users', value: 'no' },
                    { text: 'Manual', value: 'manual' },
                    { text: 'Random', value: 'random' },
                    { text: 'OIDC', value: 'oidc' }
                ]
            };
        },

        computed: {
            ...mapGetters(['selectedNewInstance']),
            checkShowAdd() {
                const users = this.selectedNewInstance.configuration.users;
                if (users.length === 0) {
                    return true;
                }
                const lastUser = users[users.length - 1];
                return (this.selectedNewInstance.configuration.usermanagement && lastUser.username !== '' || lastUser.password !== '');
            },

            additionalPythonLibraries: libraryAccessor('Python'),
            additionalRLibraries: libraryAccessor('R')
        },
        
        methods: {
            addRow() {
                this.selectedNewInstance.configuration.users.push({ username: '', password: '' });
            },
            deleteRow(user) {
                const users = this.selectedNewInstance.configuration.users;
                users.splice(users.indexOf(user), 1);
            },
            
            getInstanceCostsPerHour(){
                return CostService.getCostsPerMinutes(this.selectedNewInstance.configuration, 60);
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