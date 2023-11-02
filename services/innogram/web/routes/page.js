const express = require('express');
const router = express.Router();
const multer = require('multer');
const crypto = require('crypto');
const path = require('path');
const User = require('../models/User');
const Post = require('../models/Post');
const logger = require('../utils/logger');
const checkAuth = require('../middleware/checkAuth');


const storage = multer.diskStorage({
    destination: function (req, file, cb) {
        cb(null, './uploads')
    },
    filename: function (req, file, cb) {
        crypto.pseudoRandomBytes(16, function (err, raw) {
            cb(null, raw.toString('hex') + path.extname(file.originalname));
        });
    }
});

const upload = multer({
    storage: storage,
    fileFilter: function (req, file, cb) {
        if (!file.originalname.match(/\.(jpg|jpeg|png)$/)) {
            return cb(new Error('Only image files are allowed!'), false);
        }
        cb(null, true);
    }
});

router.get('/', checkAuth, async function (req, res) {
    try {
        const user = await User.getUserById(req.session.userId);
        res.render('feed', { username: user.username, userId: user.id });
    } catch (err) {
        console.error(err);
        res.send('Error fetching data');
    }
});

router.get('/registration', function (req, res) {
    res.render('registration');
});

router.post('/registration', async function (req, res) {
    try {
        const username = req.body.username;
        const password = req.body.password;
        if (username.length < 3 || username.length > 50) {
            return res.status(400).send("Username must be between 3 and 50 characters");
        }
        if (password.length < 3 || password.length > 50) {
            return res.status(400).send("Password must be between 3 and 50 characters");
        }
        if ((await User.getUserByUsername(username)) == null) {
            await User.createUser(username, password);
            const user = await User.getUserByUsername(username);
            req.session.userId = user.id;
            logger.info(`New user registered: ${username}`);
            res.redirect('/');
        }
        else {
            res.status(403).send("User already exists");
        }
    } catch (err) {
        res.send(err);
    }
});

router.get('/login', function (req, res) {
    res.render('login');
});

router.post('/login', async function (req, res) {
    const username = req.body.username;
    const password = req.body.password;

    try {
        const user = await User.getUserByUsername(username);
        if (await User.comparePassword(password, user.password)) {
            req.session.userId = user.id;
            logger.info(`User logged in: ${username}`);
            res.redirect('/');
        } else {
            res.send('Login failed');
        }
    } catch (err) {
        res.send('Login failed');
    }
});

router.get('/create', checkAuth, async function (req, res) {
    const user = await User.getUserById(req.session.userId);
    res.render('create', { username: user.username });
});

router.post('/create', checkAuth, upload.single('image'), async function (req, res) {
    try {
        if (req.file.size > 30 * 1024) {
            return res.status(400).send('File is too large. Maximum size is 30KB.');
        }
        const isPrivate = req.body.private === 'on';
        const description = req.body.description;
        const image = req.file.filename;
        const username = (await User.getUserById(req.session.userId)).username;
        await Post.createPost(req.session.userId, username, isPrivate, image, description);
        logger.info(`New post created by user. Username: ${username}; isPrivate: ${isPrivate}; imageFilename: ${image}; Description: ${description}`);
        res.redirect('/');
    } catch (err) {
        console.error(err);
        res.send('Error creating post');
    }
});

router.get('/user/:username', checkAuth, async function (req, res) {
    try {
        const user = await User.getUserById(req.session.userId);
        res.render('profile', { username: req.params.username, selfusername: user.username });
    } catch (err) {
        console.error(err);
        res.send('Error fetching user');
    }
});

router.get('/user/:username/:post_id', checkAuth, async function (req, res) {
    try {
        const user = await User.getUserById(req.session.userId);
        res.render('post', { username: req.params.username, post_id: req.params.post_id, selfusername: user.username });
    } catch (err) {
        console.error(err);
        res.send('Error fetching user');
    }
});

router.get('/search', checkAuth, async function (req, res) {
    const user = await User.getUserById(req.session.userId);
    res.render('search', { selfusername: user.username });
});

module.exports = router;
