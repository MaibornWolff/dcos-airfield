const notebooks = [];
const generatedNotebooks = {};

module.exports = {
    addNotebook(notebookId) { // add notebook to store - that means export from instance
        if (notebookId in generatedNotebooks) {
            generatedNotebooks[notebookId]['created_at'] = Math.round((new Date()).getTime() / 1000);
            notebooks.push(generatedNotebooks[notebookId]);
            delete generatedNotebooks[notebookId];
            return true;
        }
        return false;
    },
    
    generateNotebook() {
        const notebook = {
            name: 'Notebook ' + Math.random().toString(36).replace(/[^a-z]+/g, ''),
            id: Math.random().toString(36).replace(/[^a-z]+/g, ''),
            creator: 'anonymous'
        };
        generatedNotebooks[notebook.id] = notebook;
        return notebook;
    },
    
    get() {
        return notebooks;
    }
    
};