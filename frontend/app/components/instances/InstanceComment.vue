<template>
    <div>
        <template v-if="row.item._commit">
            <b-input-group v-if="!isLoading">
                <b-form-input v-model="row.item.details.comment" type="text" placeholder="Comment" autofocus></b-form-input>
                <b-input-group-append>
                    <b-button variant="secondary" @click="commitInstance(row.item.details.comment)">
                        <fa icon="comment"></fa> Save comment
                    </b-button>
                    <b-button variant="outline-danger" @click="toggle()">
                        <fa icon="comment-slash"></fa> Reset comment
                    </b-button>
                </b-input-group-append>
            </b-input-group>
            <fa icon="spinner" spin v-if="isLoading"></fa>
        </template>
        <label v-else>{{ row.item.details.comment }}</label>
    </div>
</template>

<script>
    import Vue from 'vue';
    
    
    export default {
        name: 'InstanceComment',
        
        props: {
            row: {
                type: Object,
                required: true
            }
        },
        
        data(){
            return {
                isLoading: false
            };
        },
        
        methods: {
            close(){
                Vue.set(this.row.item, '_commit', false);
            },
            
            open(){
                Vue.set(this.row.item, '_commit', true);
            },
            
            async toggle(){
                if(this.row.item._commit){
                    await this.resetComment();
                    this.close();
                }
                else {
                    this.open();
                }
            },
            
            async resetComment(){
                const id = this.row.item.instance_id;
                try {
                    this.isLoading = true;
                    await this.$store.dispatch('resetComment', id);
                    this.$eventBus.$emit('showSuccessToast', `Comment resetted successfully!`);
                }
                catch (e) {
                    this.$eventBus.$emit('showErrorToast', `Error resetting the comment!`);
                }
                finally {
                    this.isLoading = false;
                }
            },

            async commitInstance(comment){
                try {
                    this.isLoading = true;
                    await this.$store.dispatch('commitInstance', { instanceId: this.row.item.instance_id, comment: comment });
                    this.$eventBus.$emit('showSuccessToast', `Instance committed successfully!`);
                }
                catch (e) {
                    this.$eventBus.$emit('showErrorToast', `Error committing the instance! Trying to reset the comment!`);
                    this.resetComment();
                }
                finally {
                    this.isLoading = false;
                    this.close();
                }
            }
        }
    };
</script>

<style scoped>

</style>