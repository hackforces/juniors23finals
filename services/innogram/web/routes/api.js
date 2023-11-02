const express = require('express');
const router = express.Router();
const User = require('../models/User');
const Post = require('../models/Post');
const Comment = require('../models/Comment');
const logger = require('../utils/logger');
const checkAuth = require('../middleware/checkAuth');


router.get('/feed', checkAuth, async function (req, res) {
    try {
        const user = await User.getUserById(req.session.userId);
        const posts = await Post.getAccessiblePosts(user.id, 35);
        res.json(posts);
    } catch (err) {
        console.error(err);
        res.status(500).send({ error: 'Error fetching data' });
    }
});

router.get('/getNewProfiles', checkAuth, async function (req, res) {
    try {
        const profiles = await User.getNewProfiles();
        res.json(profiles);
    } catch (err) {
        console.error(err);
        res.status(500).send({ error: 'Error fetching data' });
    }
});

router.get('/user/:username', checkAuth, async function (req, res) {
    try {
        const user = await User.getUserByUsername(req.params.username);
        const currUser = await User.getUserById(req.session.userId);
        var subscriptionStatus = "myself";
        if (currUser.id != user.id) {
            subscriptionStatus = req.session.userId && currUser.subscribed_to
                ? (currUser.subscribed_to.includes(user.id) ? "subscribed" : "unsubscribed")
                : "unsubscribed";
        }
        if (!user) {
            return res.status(404).send({ error: 'User does not exist' });
        }
        const posts = await Post.getAccessiblePostsByUserId(req.session.userId, user.id);

        const userData = {
            id: user.id,
            username: user.username,
            posts: posts,
            subscriptionStatus: subscriptionStatus
        };

        res.json(userData);
    } catch (err) {
        console.error(err);
        res.status(500).send({ error: 'Error fetching data' });
    }
});

router.get('/user/:username/:post_id', checkAuth, async function (req, res) {
    try {
        const user = await User.getUserByUsername(req.params.username);
        if (!user) {
            return res.status(404).send({ error: 'User does not exist' });
        }
        const post = await Post.getPostById(req.params.username, req.params.post_id);
        if (!post) {
            return res.status(404).send({ error: 'Post does not exist' });
        }
        const comments = await Comment.getCommentsByPostId(post.uid);
        const isLiked = (post.likes) ? post.likes.includes(req.session.userId) : false;
        const postData = {
            username: user.username,
            post: post,
            comments: comments,
            isLiked: isLiked
        };

        res.json(postData);
    } catch (err) {
        console.error(err);
        res.status(500).send({ error: 'Error fetching data' });
    }
});

router.post('/subscribe', checkAuth, async function (req, res) {
    try {
        const userId = req.session.userId;
        const subscribeId = req.body.id;
        if (!userId || !subscribeId) {
            return res.status(400).json({ error: 'Invalid request' });
        }
        const user = await User.getUserById(req.session.userId);
        if (!user.subscribed_to || !user.subscribed_to.includes(subscribeId)) {
            await User.subscribeUser(userId, subscribeId);
            logger.info(`UserId ${userId} subscribed to UserId ${subscribeId}`);
            res.json({ success: true });
        }
        else {
            res.status(409).json({ error: "Already subscribed" })
        }
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: 'An error occurred while subscribing.' });
    }
});

router.post('/unsubscribe', checkAuth, async function (req, res) {
    try {
        const userId = req.session.userId;
        const unSubscribeId = req.body.id;
        if (!userId || !unSubscribeId) {
            return res.status(400).json({ error: 'Invalid request' });
        }
        const user = await User.getUserById(req.session.userId);
        if (user.subscribed_to && user.subscribed_to.includes(unSubscribeId)) {
            await User.unsubscribeUser(userId, unSubscribeId);
            logger.info(`UserId ${userId} unsubscribed from UserId ${unSubscribeId}`);
            res.json({ success: true });
        }
        else {
            res.status(409).json({ error: "Not subscribed" })
        }
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: 'An error occurred while unsubscribing.' });
    }
});

router.post('/comment', checkAuth, async function (req, res) {
    try {
        const userId = req.session.userId;
        const { comment, post_owner_username, post_id } = req.body;
        if (!userId || !comment || !post_owner_username || !post_id) {
            return res.status(400).json({ error: 'Invalid request' });
        }
        await Comment.createComment(userId, post_owner_username, post_id, comment);
        logger.info(`New comment created by user ${userId} on post ${post_id}: ${comment}`);
        res.json({ success: true });
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: 'An error occurred while posting comment.' });
    }
});

router.post('/like', checkAuth, async function (req, res) {
    try {
        const { username, post_id } = req.body;
        await Post.likePost(req.session.userId, username, post_id);
        logger.info(`UserId ${req.session.userId} clicked like on post ${post_id}`);
        res.json({ success: true });
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: 'An error occurred while liking the post.' });
    }
});

router.get('/search', checkAuth, async function (req, res) {
    try {
        const { query } = req.query;
        if (!query) {
            return res.status(400).json({ error: 'Missing query parameter' });
        }
        const posts = await Post.searchPosts(query);
        res.json(posts);
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: 'An error occurred while searching for posts.' });
    }
});

module.exports = router;
