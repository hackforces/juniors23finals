const db = require('../db/db'); // import the database connection
const Post = require('./Post');
const User = require('./User');

class Comment {
    static async createComment(user_id, post_owner_username, post_id, comment) {
        const post = await Post.getPostById(post_owner_username, post_id);
        const username = (await User.getUserById(user_id)).username;
        const postOwner = await User.getUserById(post.owner_id);

        if (!post.private || user_id === post.owner_id || (postOwner.subscribed_to && postOwner.subscribed_to.includes(user_id))) {
            await db.none('INSERT INTO comments(post_uid, user_id, username, comment) VALUES($1, $2, $3, $4)', [post.uid, user_id, username, comment]);
        } else {
            throw new Error('Cannot comment on a private post that you do not own or are not subscribed to.');
        }
    }

    static async getCommentsByPostId(postUid) {
        const comments = await db.any('SELECT * FROM comments WHERE post_uid = $1 ORDER BY id', [postUid]);
        return comments;
    }
}

module.exports = Comment;
