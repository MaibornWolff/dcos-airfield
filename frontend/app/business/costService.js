

export default{
    getNumberOfCPUCores(configuration) {
        return +configuration.cpus + +configuration.env.SPARK_CORES_MAX * +configuration.instances;
    },

    getNumberOfRAM(configuration) {
        return (+configuration.mem + 1024 * parseFloat(configuration.env.SPARK_EXECUTOR_MEMORY) * +configuration.instances) / 1000;
    },
    
    getCostsPerMinute(configuration) {
        const ram = this.getNumberOfRAM(configuration);
        const cpu = this.getNumberOfCPUCores(configuration);
        const ramPerMinute = configuration.costsAsObject.ram_in_gb_per_minute;
        const cpuPerMinute = configuration.costsAsObject.core_per_minute;
        return ram * ramPerMinute + cpu * cpuPerMinute;
    },
    
    getCostsPerMinutes(configuration, minutes) {
        return this.getCostsPerMinute(configuration) * minutes;
    }
};