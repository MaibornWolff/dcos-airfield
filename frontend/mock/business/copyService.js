module.exports = {
    copy(object){
        let obj;
        if(object && typeof object === 'object'){
            if(Array.isArray(object)){
                obj = [];
                object.forEach(element => obj.push(this.copy(element)));
            }
            else{
                obj = {};
                Object.keys(object).forEach(key => {
                    if(typeof object[key] === 'object'){
                        obj[key] = this.copy(object[key]);
                    }
                    else {
                        obj[key] = object[key];
                    }
                });
            }
        }
        return obj || object;
    }
};