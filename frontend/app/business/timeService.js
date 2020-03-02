import moment from 'moment';

export default{
    humanizeTimestamp(sec){
        return moment.duration(sec, 'seconds').humanize();
    }
};