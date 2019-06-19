<template>
    <div class="buttonCol">
        <template v-if="isCommit">
            <b-col sm="10">
                <b-form-input
                    v-model="newComment"
                    placeholder="comment"
                    type="text"></b-form-input>
            </b-col>
            <b-button
                v-for="action in actions" :key="action.key"
                v-if="action.key === 'commit'"
                size="sm"
                class="mx-1"
                :variant="action.variant"
                :disabled="actionInProgress"
                @click="triggerAction(action)">
                <fa :icon="action.icon"></fa>
                {{ action.name }}
            </b-button>
        </template>
        <b-dropdown text="Buttons" class="m-2" variant="primary" right size="sm">
            <b-dropdown-item-button
                v-for="action in actions" :key="action.key"
                size="sm"
                class="mx-1"
                :variant="action.variant"
                :disabled="actionInProgress"
                @click="triggerAction(action)">
                <fa :icon="action.icon"></fa>
                {{ action.name }}
            </b-dropdown-item-button>
            <template v-if="typeof item.deleted_at === 'undefined'">
                <b-dropdown-item-button v-if="item.configuration.users.length > 0" variant="info" size="sm"
                                        class="mx-1" @click="showPasswords()">
                    <fa icon="lock-open"></fa> Passwords
                </b-dropdown-item-button>
                <b-dropdown-item-button v-if="item.status === 'HEALTHY'" size="sm" class="mx-1" variant="primary" @click="triggerAction({key: 'import', name: 'import'})"><fa icon="download"></fa> Import</b-dropdown-item-button>
                <b-dropdown-item-button v-if="item.status === 'HEALTHY'" size="sm" class="mx-1" variant="primary" @click="triggerAction({key: 'export', name: 'export'})"><fa icon="upload"></fa> Export</b-dropdown-item-button>
            </template>
        </b-dropdown>
        <fa icon="spinner" spin v-if="actionInProgress"></fa>
    </div>
</template>

<script>
    import Vue from 'vue';
    import Server from '@/server';

    export default {
        name: 'InstanceButtons',
        props: {
            item: {
                type: Object,
                required: true
            }
            
        },
        data() {
            return {
                isLoading: false,
                actionInProgress: false,
                isCommit: false,
                newComment: this.item.comment,
                actions: typeof this.item.deleted_at !== 'undefined' ? [
                        { key: 'delete', name: 'Delete', variant: 'danger', icon: 'trash-alt' }
                ] : [
                    { key: 'start', name: 'Start', variant: 'success', icon: 'play' },
                    { key: 'restart', name: 'Restart', variant: 'success', icon: 'play-circle' },
                    { key: 'stop', name: 'Stop', variant: 'warning', icon: 'stop' },
                    { key: 'delete', name: 'Delete', variant: 'danger', icon: 'trash-alt' },
                    { key: 'redeploy', name: 'Reconfigure', variant: 'danger', icon: 'cog' },
                    { key: 'commit', name: 'Commit', variant: 'secondary', icon: 'comment' }
                ]
            };
        },
        methods: {
            async triggerAction(action) {
                try {
                    Vue.set(this, 'actionInProgress', true);
                    if (action.key === 'commit') {
                        if(this.isCommit){
                            await this.commitInstance();
                        }
                        Vue.set(this, 'isCommit', !this.isCommit);
                    }
                    else if (action.key === 'redeploy') {
                        this.$router.push('/redeploy/' + this.item.id);
                    }
                    else if (action.key === 'import') {
                        this.$emit('show-import');
                    }
                    else if (action.key === 'export') {
                        this.$emit('show-export');
                    }
                    else {
                        if(typeof this.item.deleted_at !== 'undefined'){
                            await Server.deleteInstanceFromDeletedInstances(this.item.id);
                        }
                        else {
                            await Server.triggerInstanceAction(action.key, this.item.id);
                        }
                        
                        this.$eventBus.$emit('showSuccessToast', `Action "${action.name}" executed successfully.`);

                        if (action.key === 'delete') {
                            if(typeof this.item.deleted_at !== 'undefined'){
                                this.$emit('load-deleted-instances');
                            }
                            else {
                                this.$emit('load-existing-instances');
                            }
                        }
                        else {
                            Vue.set(this.item, 'status', '');
                            this.$emit('get-instance-state', this.item);
                        }
                    }
                }
                catch (e) {
                    this.$eventBus.$emit('showErrorToast', `Error executing action "${action.name}". "${e}"`);
                }
                finally {
                    Vue.set(this, 'actionInProgress', false);
                }
            },
            
            showPasswords() {
                this.$emit('show-passwords');
            },
            
            async commitInstance(){
                if (this.item.comment === this.newComment){
                    return;
                }
                const oldComment = this.item.comment;
                try {
                    this.item.comment_only = true; // eslint-disable-line
                    this.item.comment = this.newComment;
                    await Server.createNewInstance(this.item);
                    this.$eventBus.$emit('showSuccessToast', 'Instance committed successfully.');
                }
                catch (e) {
                    this.item.comment = oldComment;
                    this.$eventBus.$emit('showErrorToast', 'Error committing the instance!');
                }
                finally {
                    Vue.delete(this.item, 'comment_only');
                }
            }
        }

        
    };
</script>

<style lang="scss" scoped>
    .buttonCol{
        .m-2 {
            .mx-1:hover {
                background: black;
            }
        }
    }

</style>