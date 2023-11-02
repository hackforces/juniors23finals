const db = require('../db/db'); // import the database connection
const bcrypt = require('bcrypt');

class User {
  static async createUser(username, password) {
    const hash = await bcrypt.hash(password, 10);
    await db.none('INSERT INTO users(username, password) VALUES($1, $2)', [username, hash]);
  }

  static async getUserByUsername(username) {
    return await db.oneOrNone('SELECT * FROM users WHERE username = $1', [username]);
  }
  
  static async getUserById(id) {
    return await db.oneOrNone('SELECT * FROM users WHERE id = $1', [id]);
  }

  static async getNewProfiles() {
    // This is just an example. Replace this with your actual logic to get new profiles.
    return await db.any('SELECT * FROM users ORDER BY id DESC LIMIT 10');
  }

  static async comparePassword(password, hash) {
    return await bcrypt.compare(password, hash);
  }

  static async subscribeUser(userId, subscribeId) {
    await db.none('UPDATE users SET subscribed_to = array_append(subscribed_to, $1) WHERE id = $2', [subscribeId, userId]);
  }

  static async unsubscribeUser(userId, subscribeId) {
    await db.none('UPDATE users SET subscribed_to = array_remove(subscribed_to, $1) WHERE id = $2', [subscribeId, userId]);
  }
}

module.exports = User;
