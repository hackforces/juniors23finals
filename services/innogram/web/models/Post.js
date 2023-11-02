const db = require('../db/db'); // import the database connection

class Post {
    static async createPost(owner, ownerUsername, isPrivate, image, description) {
        await db.none('INSERT INTO posts(owner_id, owner_username, private, image, description) VALUES($1, $2, $3, $4, $5)', [owner, ownerUsername, isPrivate, image, description]);
    }

    static async getPostById(username, post_id) {
        const accessiblePosts = await db.oneOrNone(`
        SELECT * FROM posts
        WHERE owner_username = $1 
        AND post_id = $2`, [username, post_id]);
        
        return accessiblePosts;
    }

    static async getAccessiblePostsByUserId(requesterId, userId) {
        const accessiblePosts = await db.any(`
        SELECT * FROM posts
        WHERE owner_id = $2 
        AND (
            NOT private 
            OR $1 IN (
                SELECT unnest(subscribed_to) FROM users WHERE id = owner_id
            )
            OR owner_id = $1
        )
        ORDER BY uid`, [requesterId, userId]);
        
        return accessiblePosts;
    }

    static async getAccessiblePosts(requesterId, limit) {
        // Get all posts that the user is allowed to see
        const accessiblePosts = await db.any(`
          SELECT * FROM posts 
          WHERE NOT private 
          OR $1 IN (
            SELECT unnest(subscribed_to) FROM users WHERE id = owner_id
          )
          OR $1 = owner_id
          ORDER BY uid DESC 
          LIMIT $2
        `, [requesterId, limit]);
      
        return accessiblePosts;
      }

    static async searchPosts(query) {
        const posts = await db.any(`
            SELECT * FROM posts 
            WHERE description ~ $1
            ORDER BY uid DESC
            LIMIT 35
        `, [query]);
        return posts;
    }
  
    static async likePost(userId, username, post_id) {
        await db.none(`
            UPDATE posts 
            SET likes = CASE 
                WHEN $1 = ANY(likes) THEN array_remove(likes, $1)
                ELSE array_append(likes, $1)
            END
            WHERE owner_username = $2 AND post_id = $3 AND (
                NOT private 
                OR $1 IN (
                    SELECT unnest(subscribed_to) FROM users WHERE id = owner_id
                )
                OR owner_id = $1
            )
        `, [userId, username, post_id]);
    }

}

module.exports = Post;
