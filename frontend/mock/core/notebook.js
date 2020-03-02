/* eslint-disable camelcase */

const notebooks = {};


module.exports = {
    addNotebook(payload) { // add notebook to store - that means export from instance
        const instanceId = payload.instanceId;
        const notebookId = payload.notebookId || Math.random().toString(36).replace(/[^a-z]+/g, '');
        if(!instanceId){
            throw Error('No instance id given!');
        }
        let index = -1;
        if(!(instanceId in notebooks)){
            notebooks[instanceId] = [];
        }
        else{
            index = notebooks[instanceId].findIndex(v => v.id === notebookId);
        }
        const notebook = this.generateNotebook(notebookId);
        if(index !== -1){
            notebooks[instanceId].splice(index, 1, notebook);
            return true;
        }
        notebooks[instanceId].push(notebook);
        return false;
    },
    
    generateNotebook(notebookId) {
        return {
            name: 'Notebook ' + notebookId,
            id: notebookId
        };
    },
    
    deleteNotebook(notebookId){
        // eslint-disable-next-line guard-for-in
        for(const instanceId of Object.keys(notebooks)){
            const index = notebooks[instanceId].findIndex(notebook => notebook.id === notebookId);
            if(index !== -1){
                notebooks[instanceId].splice(index, 1);
                break;
            }
        }
    },
    
    get(instanceId) {
        if(instanceId === undefined){
            const allNotebooks = [];
            Object.keys(notebooks).forEach(id => notebooks[id].forEach(nb => allNotebooks.push(nb)));
            return allNotebooks;
        }
        return notebooks[instanceId] || [];
    },
    
    notebookExists(payload){
        const instanceId = payload.instanceId;
        const notebookId = payload.notebookId;
        if(!instanceId){
            throw Error('No instance id given!');
        }
        if(!notebookId){
            throw Error('No notebook id given');
        }
        if(!notebooks[instanceId]){
            return false;
        }
        return !!notebooks[instanceId].find(v => v.id === notebookId);
    }
    
};