const deletedInstances = [];
const instances = [];
const states = {};


function getRandomArrayElement(array) {
    return array[Math.floor(Math.random() * array.length)];
}

function getRandomState() {
    return getRandomArrayElement(['NOT_FOUND', 'UNHEALTHY', 'STOPPED', 'DEPLOYING', 'HEALTHY']);
}

function generateId() {
    return Math.random().toString(36).replace(/[^a-z]+/g, '');
}

function createHistoryObject(instance, newStatus, time) {
    return {
        status: newStatus === 'STOPPED' ? 'STOPPED' : 'RUNNING',
        time: typeof time === 'undefined' ? Math.floor(Date.now() / 1000) : time,
        resources: {
            zeppelin: {
                cpus: instance.configuration.cpus,
                mem: instance.configuration.mem
            },
            spark: {
                cpus: instance.configuration.env.SPARK_CORES_MAX,
                mem: instance.configuration.env.SPARK_EXECUTOR_MEMORY
            }
        }
    };
}

function createGeneratedInstance(id, createdAt, deletedAt) {
    const users = Math.random() >= 0.5 ? [{ username: 'admin', password: 'admin' }, {
        username: 'guest',
        password: '123'
    }] : [];
    const instance = {
        template_id: 2,
        createdBy: 'Host',
        id,
        url: 'https://example.com/id-' + id,
        comment: getRandomArrayElement([
            'Lorem ipsum dolor sit amet',
            'consectetur adipiscing elit, sed do eiusmod tempor',
            'foobar',
            ''
        ]),
        created_at: typeof createdAt === 'undefined' ? Math.floor(Date.now() / 1000) - 120 : createdAt, // -120 makes debugging of detecting stuck deployments easier
        history: [],
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
            users: users
        }
    };
    if (typeof deletedAt !== 'undefined'){
        instance.deleted_at = deletedAt;
    }
    return instance;
}

module.exports = {
    
    add(instance) {
        if (typeof instance.deleted_at === 'undefined'){
            const id = generateId();
            instances.push({
                id,
                comment: instance.comment,
                url: 'https://example.com/id-' + id,
                created_at: Math.floor(Date.now() / 1000) - 120,
                configuration: instance.configuration,
                createdBy: instance.createdBy,
                history: [createHistoryObject(instance, 'RUNNING')],
                template_id: instance.template_id
            });
            states[id] = 'DEPLOYING';
        }
        else {
            this.deletedInstances.push(instance);
        }
    },

    updateHistory(id) {
        const newStatus = states[id];
        for (let i = 0; i < instances.length; i++) {
            if (instances[i].id === id) {
                instances[i].history.push(createHistoryObject(instances[i], newStatus));
                return;
            }
        }
    },

    updateOrAddInstance(instance) {
        for (let i = 0; i < instances.length; i++) {
            if (instances[i].id === instance.id) {
                instance._showDetails = false;
                instances[i] = instance;
                if (!instances[i].comment_only) {
                    instances[i].history.push(createHistoryObject(instances[i], 'STOPPED'));
                    instances[i].history.push(createHistoryObject(instances[i], 'RUNNING'));
                }
                delete instances[i].comment_only;
                return false;
            }
        }
        this.add(instance);
        return true;
    },

    get(type) {
        if(typeof type === 'undefined' || type.toUpperCase().includes('EXISTING')){
            return instances;
        }
        else if(type.toUpperCase().includes('DELETED')){
            return deletedInstances;
        }
        return undefined;
    },

    getState(id) {
        return states[id];
    },

    deleteFromDeletedInstances(id){
        const index = deletedInstances.findIndex(e => e.id === id);
        if (index > -1) {
            deletedInstances.splice(index, 1);
        }
    },

    action(action, id) {
        switch (action) {
            case 'start':
            case 'restart':
                states[id] = 'HEALTHY';
                this.updateHistory(id);
                break;

            case 'stop':
                states[id] = 'STOPPED';
                this.updateHistory(id);
                break;

            case 'delete':
                const index = instances.findIndex(e => e.id === id);
                if (index > -1) {
                    instances[index].deleted_at = Math.floor(Date.now() / 1000);
                    deletedInstances.push(instances[index]);
                    instances.splice(index, 1);
                }
                delete states[id];
                break;
            default:
                console.log('Action not accepted: ' + action); // eslint-disable-line
                break;
        }
    }
};


for (let i = 0, l = Math.round(Math.random() * 10 + 1); i < l; ++i) {
    const id = generateId();
    const state = getRandomState();
    const instance = createGeneratedInstance(id);
    instance.history.push(createHistoryObject(instance, state));
    instances.push(instance);
    states[id] = state;
}

for (let i = 0, l = Math.round(Math.random() * 10 + 1); i < l; ++i) {
    const state = getRandomState();
    const id = generateId();
    const instance = createGeneratedInstance(id, Math.floor(Date.now() / 1000 - 120000), Math.floor(Date.now() / 1000) - 120);
    instance.history.push(createHistoryObject(instance, state, Math.floor(Date.now() / 1000 - 120000)));
    deletedInstances.push(instance);
}
