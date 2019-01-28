const instances = [];
const states = { };

function getRandomArrayElement(array) {
    return array[Math.floor(Math.random() * array.length)];
}

function getRandomState() {
    return getRandomArrayElement(['NOT_FOUND', 'UNHEALTHY', 'STOPPED', 'DEPLOYING', 'HEALTHY']);
}

function generateId() {
    return Math.random().toString(36).replace(/[^a-z]+/g, '');
}

for (let i = 0, l = Math.round(Math.random() * 10 + 1); i < l; ++i) {
    const id = Math.random().toString(36).replace(/[^a-z]+/g, '');
    const users = Math.random() >= 0.5 ? [{ username: 'admin', password: 'admin' }, { username: 'guest', password: '123' }] : [];
    instances.push({
        template_id: 2,
        id,
        url: 'https://example.com/id-' + id,
        comment: getRandomArrayElement([
            'Lorem ipsum dolor sit amet',
            'consectetur adipiscing elit, sed do eiusmod tempor',
            'foobar',
            ''
        ]),
        created_at: Math.floor(Date.now() / 1000) - 120, // -120 makes debugging of detecting stuck deployments easier
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
            mem: 16384,
            usermanagement: 'random',
            users: users
        }
    });
    states[id] = getRandomState();
}

module.exports = {
    add(instance) {
        const id = generateId();
        instances.push({
            id,
            comment: instance.comment,
            url: 'https://example.com/id-' + id,
            created_at: Math.floor(Date.now() / 1000) - 120,
            configuration: instance.configuration,
            template_id: instance.template_id
        });
        states[id] = 'DEPLOYING';
    },

    updateOrAddInstance(instance) {
        for (let i = 0; i < instances.length; i++) {
            if (instances[i].id === instance.id) {
                instances[i] = instance;
                return false;
            }
        }
        this.add(instance);
        return true;
    },
    
    get() {
        return instances;
    },

    getState(id) {
        return states[id];
    },

    action(action, id) {
        switch (action) {
            case 'start':
            case 'restart':
                states[id] = 'HEALTHY';
                break;
                
            case 'stop':
                states[id] = 'STOPPED';
                break;

            case 'delete':
                const index = instances.findIndex(e => e.id === id);
                if (index > -1) {
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