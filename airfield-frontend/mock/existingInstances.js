const instances = [];
const states = { };

function getRandomArrayElement(array) {
    return array[Math.floor(Math.random() * array.length)];
}

function getRandomState() {
    return getRandomArrayElement(['NOT_FOUND', 'RUNNING', 'STOPPED']);
}

for (let i = 0, l = Math.round(Math.random() * 10 + 1); i < l; ++i) {
    const id = i + 1;
    instances.push({
        id,
        url: 'https://example.com/id-' + id,
        comment: getRandomArrayElement([
            'Lorem ipsum dolor sit amet',
            'consectetur adipiscing elit, sed do eiusmod tempor',
            'foobar',
            ''
        ])
    });
    states[id] = getRandomState();
}

module.exports = {
    add(instance) {
        const id = Math.max(...instances.map(e => e.id)) + 1;
        instances.push({
            id,
            comment: instance.comment,
            url: 'https://example.com/id-' + id
        });
        states[id] = getRandomState();
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
                states[id] = 'RUNNING';
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
        }
    }
};