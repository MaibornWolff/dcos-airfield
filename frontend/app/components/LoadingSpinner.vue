<template>
    <div>
        <div>
            <fa icon="spinner" size="2x" spin></fa>
            <span>Loading...</span>
        </div>
    </div>
</template>


<script>
    export default { };
</script>


<style lang="scss" scoped>
    div {
        div {
            display: flex;
            flex-direction: row;
            align-items: center;
            margin: 0 auto;
        }

        span {
            display: inline-block;
            margin-left: 10px;
            font-weight: bold;
            font-size: 1.1rem;
        }
    }
</style>