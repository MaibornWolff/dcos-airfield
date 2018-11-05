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
        mem: 8192
    },
    icon: 'small',
    id: 1,
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
        mem: 32768
    },
    icon: 'medium',
    id: 2,
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
        mem: 32768
    },
    icon: 'large',
    id: 3,
    tags: ['Large', 'No Libs'],
    title: 'Large'
}];