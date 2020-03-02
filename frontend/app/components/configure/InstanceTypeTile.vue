<template>
    <div class="tile m-1" :class="{ selected: isSelected }" @click="onInstanceSelected">
        <div class="title">
            <fa :icon="icon"></fa>
            <span>{{ instance.title }}</span>
        </div>

        <div>
            <b-badge
                v-for="(tag, index) in instance.tags" :key="index"
                variant="primary"
                class="m-1"
            >
                {{ tag }}
            </b-badge>
        </div>
    </div>
</template>


<script>
    import { mapGetters } from 'vuex';

    export default {
        props: {
            instance: {
                type: Object,
                required: true
            }
        },
        
        computed: {
            ...mapGetters(['selectedNewInstance']),

            isSelected() {
                return this.selectedNewInstance.template_id === this.instance.template_id;
            },

            icon() {
                switch (this.instance.icon) {
                    case 'small':
                        return 'home';
                    case 'medium':
                        return 'building';
                    case 'large':
                        return 'industry';
                    default:
                        return 'question-circle';
                }
            }
        },

        methods: {
            onInstanceSelected() {
                this.$store.dispatch('selectNewInstance', this.instance.configuration);
            }
        }
    };
</script>


<style lang="scss" scoped>
    @import "~@/assets/styles/variables";

    .tile {
        display: flex;
        flex-direction: column;
        align-items: center;
        min-width: 200px;
        border: 1px solid $bs-color-card-border;
        border-radius: 4px;
        text-align: center;
        padding: 5px 10px;
        cursor: pointer;

        &:hover, &.selected {
            color: $color-primary;
            border-color: $color-primary;
        }
    }

    .title {
        display: flex;
        flex-direction: row;
        align-items: center;
        font-size: 1.1rem;
        font-weight: bold;

        svg {
            width: 1.5em;
            height: 1.5em;
        }

        span {
            display: inline-block;
            margin-left: 10px;
        }
    }
</style>