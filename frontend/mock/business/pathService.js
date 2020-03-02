module.exports = {
    getElementOfPath(path, index = 3) { // id is mostly at position 3
        const pathParts = path.split('/');
        return pathParts[index];
    }
};