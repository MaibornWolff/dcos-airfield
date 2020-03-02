/* eslint-disable camelcase */
import Server from '@/server/index';

const axiosInstance = Server.axiosInstance;
const NOTEBOOK_PATH = Server.NOTEBOOK_PATH;
const INSTANCE_PATH = Server.INSTANCE_PATH;


export default {
    async getNotebooks() {
        const response = await axiosInstance.get(NOTEBOOK_PATH);
        return response.data.notebooks;
    },

    async getInstanceNotebooks(instanceId) {
        const response = await axiosInstance.get([INSTANCE_PATH, instanceId, NOTEBOOK_PATH].join('/'));
        return response.data.notebooks;
    },

    async importNotebook(payload) {
        const instanceId = payload.instanceId;
        const notebookId = payload.notebookId;
        const response = await axiosInstance.post([NOTEBOOK_PATH, notebookId, 'import'].join('/'), { instance_id: instanceId });
        return response.status;
    },

    async deleteNotebook(payload) {
        const notebookId = payload.notebookId;
        const response = await axiosInstance.delete([NOTEBOOK_PATH, notebookId].join('/'));
        return response.status;
    },

    async exportNotebook(notebookId, instanceId, force = false) {
        let response;
        try{
            response = await axiosInstance.post([NOTEBOOK_PATH].join('/'),
                { data: { instance_id: instanceId, notebook_id: notebookId } }, { params: { force: force } });
        }
        catch (e) {
            return e.response.status;
        }
        return response.status;
    },
    
    async backupNotebooks(payload){
        const instanceId = payload.instanceId;
        const response = await axiosInstance.post([INSTANCE_PATH, instanceId, NOTEBOOK_PATH, 'backup'].join('/'));
        return response.status;
    },
    
    async restoreNotebooks(payload){
        const instanceId = payload.instanceId;
        const response = await axiosInstance.post([INSTANCE_PATH, instanceId, NOTEBOOK_PATH, 'restore'].join('/'));
        return response.status;
    },

    async cancelRestoreNotebooks(payload){
        const instanceId = payload.instanceId;
        const response = await axiosInstance.delete([INSTANCE_PATH, instanceId, NOTEBOOK_PATH, 'restore'].join('/'));
        return response.status;
    }

};