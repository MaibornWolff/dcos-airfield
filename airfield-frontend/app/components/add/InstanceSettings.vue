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
        </b-tabs>

        <br>
        <create-instance-button></create-instance-button>
    </div>
</template>


<script>
    import { mapGetters } from 'vuex';

    import CreateInstanceButton from '@/components/add/CreateInstanceButton';

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

        computed: {
            ...mapGetters(['selectedNewInstance']),

            additionalPythonLibraries: libraryAccessor('Python'),
            additionalRLibraries: libraryAccessor('R')
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
</style>