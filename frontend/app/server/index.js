import axios from 'axios';

export default {
    INSTANCE_PATH: 'instance',
    SECURITY_PATH: 'security',
    NOTEBOOK_PATH: 'notebook',
    axiosInstance: axios.create({
        baseURL: `/api/`
    })
};