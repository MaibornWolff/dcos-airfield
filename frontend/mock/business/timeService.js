const moment = require('moment');
    

module.exports = {
    formatRunningTime(time){
        return moment.duration(time, 'seconds').humanize();
    },
    
    toIsoString(time){
        return moment(time * 1000).toISOString(true);
    },

    now() {
        return moment().unix();
    },
    
    toSeconds(timeString){
        return moment(timeString, 'YYYY-MM-DD').unix();
    }
};