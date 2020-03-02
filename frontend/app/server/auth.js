import Server from '@/server/index';

const axiosInstance = Server.axiosInstance;
const SECURITY_PATH = Server.SECURITY_PATH;

export default {
    async getZeppelinGroups() {
        const response = await axiosInstance.get([SECURITY_PATH, 'groups'].join('/'));
        return response.data;
    },

    async getSecurityState() {
        const response = await axiosInstance.get([SECURITY_PATH, 'state'].join('/'));
        return response.data;
    }
};