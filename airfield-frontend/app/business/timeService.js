import moment from 'moment';

export default{
    formatRunningTime(time, humanize){
        if (typeof time === 'undefined') {
            return time;
        }
        const mom = moment.duration(time, 'seconds');
        if (humanize){
            return mom.humanize();
        }
        const years = mom.years() > 0 ? mom.years() + this.pluralize(' year', mom.years()) + '; ' : '';
        const months = mom.months() > 0 ? mom.months() + this.pluralize(' month', mom.months()) + '; ' : '';
        const days = mom.days() > 0 ? mom.days() + this.pluralize(' day', mom.days()) + '; ' : '';
        const hours = this.zeroPad(mom.hours()) + this.pluralize(' hour', mom.hours()) + '; ';
        const minutes = this.zeroPad(mom.minutes()) + this.pluralize(' minute', mom.minutes()) + '; ';
        const seconds = this.zeroPad(mom.seconds()) + this.pluralize(' second', mom.seconds()) + '; ';
        return years + months + days + hours + minutes + seconds;
    },
    
    zeroPad(value) {
        return ('0' + value).slice(-2);
    },
    
    pluralize(unit, value) {
        return unit + (value === 1 ? '' : 's');

    },
    
    toUTCString(time){
        return new Date(time * 1000).toString();
    }
};