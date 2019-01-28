<template>
    <b-modal ref="passwordsModalElement" hide-footer title="Zeppelin Passwords">
        <table class="table table-striped">
            <thead>
                <tr>
                    <th>Username</th>
                    <th>Password</th>
                </tr>
            </thead>
            <tbody>
                <tr v-for="(user, index) in users" :key="index">
                    <td>{{ user.username }}</td>
                    <td>{{ user.password }}</td>
                </tr>
            </tbody>
        </table>
        <b-btn class="mt-3" variant="outline-danger" block @click="dismiss()">Close</b-btn>
    </b-modal>
</template>

<script>
    export default {
        name: 'PasswordsModal',

        data() {
            return {
                users: []
            };
        },

        methods: {
            open(users) {
                this.$refs.passwordsModalElement.show();
                this.users = users;
            },

            dismiss() {
                this.$refs.passwordsModalElement.hide();
            }
        }
        
        
    };


    
</script>

<style scoped>

</style>