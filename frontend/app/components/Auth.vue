<template>
    <b-navbar-nav class="ml-auto">
        <b-nav-item-dropdown right v-if="authentication && isAuthenticated" class="mr-2">
            <template slot="button-content">
                {{ username }}
            </template>
            <b-dropdown-item href="/logout">
                Logout
            </b-dropdown-item>
        </b-nav-item-dropdown>
    </b-navbar-nav>
</template>
<script>

    import { mapState } from 'vuex';

    export default {
        computed: {
            ...mapState({ authentication: state => state.auth.authentication,
                isAuthenticated: state => state.auth.isAuthenticated,
                username: state => state.auth.username })
        },
        created() {
            this.loadSecurityState();
        },
        methods: {
            async loadSecurityState() {
                try {
                    await this.$store.dispatch('loadSecurityState');
                    if (this.authentication && !this.isAuthenticated) {
                        window.location.href = '/login';
                    }
                }
                catch (error) {
                    console.error(error); // eslint-disable-line
                    this.$eventBus.$emit('showErrorToast', 'Error loading security state!');
                }
                
            }
        }
    };
</script>
<style lang="scss" scoped>
</style>