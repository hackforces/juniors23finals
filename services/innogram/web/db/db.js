const pgp = require('pg-promise')();

const db = pgp({
  host: 'db',
  port: 5432,
  database: 'postgres',
  user: 'postgres',
  password: 'password'
});

module.exports = db;
