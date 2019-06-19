module.exports = [{
    comment: '',
    configuration: {
        cpus: 2,
        env: {
            PYSPARK_PYTHON: 'python3',
            SPARK_CORES_MAX: '2',
            SPARK_EXECUTOR_MEMORY: '2g'
        },
        instances: 1,
        libraries: [{
            language: 'Python',
            libraries: ['foo', 'bar'],
            tensorflow: false
        }, {
            language: 'R',
            libraries: []
        }],
        costsAsObject: {
            currency: 'EURO',
            core_per_minute: 0.99,
            ram_in_gb_per_minute: 0.49
        },
        mem: 8192,
        usermanagement: 'manual',
        users: [{
            username: 'admin',
            password: 'admin'
        }, {
            username: 'guest',
            password: 'guest'
        }]
    },
    icon: 'small',
    template_id: 1,
    tags: ['Small', 'No Libs'],
    title: 'Small'
}, {
    comment: '',
    configuration: {
        cpus: 4,
        env: {
            PYSPARK_PYTHON: 'python3',
            SPARK_CORES_MAX: '4',
            SPARK_EXECUTOR_MEMORY: '8g'
        },
        instances: 1,
        libraries: [{
            language: 'Python',
            libraries: [],
            tensorflow: true
        }, {
            language: 'R',
            libraries: []
        }],
        costsAsObject: {
            currency: 'EURO',
            core_per_minute: 0.99,
            ram_in_gb_per_minute: 0.49
        },
        mem: 16384,
        usermanagement: 'random',
        users: [{
            username: 'admin',
            password: ''
        }]
    },
    icon: 'medium',
    template_id: 2,
    tags: ['Medium', 'No Libs'],
    title: 'Medium'
}, {
    comment: '',
    configuration: {
        cpus: 4,
        env: {
            PYSPARK_PYTHON: 'python3',
            SPARK_CORES_MAX: '8',
            SPARK_EXECUTOR_MEMORY: '16g'
        },
        instances: 1,
        libraries: [{
            language: 'Python',
            libraries: [],
            tensorflow: false
        }, {
            language: 'R',
            libraries: []
        }],
        costsAsObject: {
            currency: 'EURO',
            core_per_minute: 0.99,
            ram_in_gb_per_minute: 0.49
        },
        mem: 32768,
        usermanagement: 'no',
        users: []
    },
    icon: 'large',
    template_id: 3,
    tags: ['Large', 'No Libs'],
    title: 'Large'
}];