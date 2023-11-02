const winston = require('winston');
const rfs = require('rotating-file-stream');
const path = require('path');

const logStream = rfs.createStream('logfile.log', {
    size: '20K',
    path: path.join(__dirname, '../logs')
});

const logger = winston.createLogger({
    level: 'info',
    format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.printf(info => `${info.timestamp}: ${info.message}`)
    ),
    transports: [
        new winston.transports.Stream({ stream: logStream })
    ]
});

module.exports = logger;
