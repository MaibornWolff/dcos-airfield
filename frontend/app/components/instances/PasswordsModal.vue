<template>
    <b-modal ref="passwordsModalElement" ok-only ok-title="Close" ok-variant="outline-danger" title="User management">
        <loading-spinner v-if="isLoading" class="mt-3"></loading-spinner>
        <template v-else>
            <table v-if="credentials" class="table table-striped">
                <thead>
                    <tr v-if="displayUsers">
                        <th>Username</th>
                        <th>Password</th>
                    </tr>
                    <tr v-else>
                        <th>Password</th>
                    </tr>
                </thead>
                <tbody v-if="displayUsers">
                    <tr v-for="(username, index) in Object.keys(credentials)" :key="index">
                        <td>{{ username }}</td>
                        <td>{{ credentials[username] }}</td>
                    </tr>
                </tbody>
                <tbody v-else>
                    <tr>
                        <td>{{ credentials }}</td>
                    </tr>
                </tbody>
            </table>
            <div v-else>
                {{ message }}
            </div>
        </template>
    </b-modal>
</template>

<script>
    import Server from '@/server/instance';

    import LoadingSpinner from '@/components/LoadingSpinner';
    export default {
        name: 'PasswordsModal',

        components: {
            LoadingSpinner
        },

        data() {
            return {
                displayUsers: false,
                isLoading: true,
                credentials: {},
                message: ''
            };
        },

        methods: {
            async loadInstanceCredentials(instanceId){
                try{
                    const credentials = await Server.getInstanceCredentials(instanceId);
                    if(credentials === null || credentials === undefined || Object.keys(credentials).length === 0){
                        this.credentials = undefined;
                    }
                    else {
                        this.credentials = credentials;
                    }
                }
                catch (e) {
                    this.$eventBus.emit('showErrorToast', 'Error loading the instance user management of ' + instanceId + '!');
                }
            },
            
            async open(instanceId) {
                this.isLoading = true;
                this.$refs.passwordsModalElement.show();
                await this.loadInstanceCredentials(instanceId);
                if(typeof this.credentials === 'object'){
                    this.displayUsers = true;
                }
                else
                if(typeof this.credentials === 'string'){
                    this.displayUsers = false;
                }
                else
                if(typeof this.credentials === 'undefined'){
                    this.message = `The instance ${instanceId} has no user management. Please redeploy the instance and create one.`;
                }
                else {
                    this.message = `Unknown type of the user management!`;
                    this.$eventBus.$emit('showErrorToast', this.message);
                }
                this.isLoading = false;
            },

            dismiss() {
                this.$refs.passwordsModalElement.hide();
            }
        }
        
        
    };


    
</script>

<style scoped>

</style>