const express = require('express');
const bodyParser = require('body-parser');
const path = require('path');
const twig = require('twig');
const session = require('express-session');
const crypto = require('crypto');
const pageRoutes = require('./routes/page');
const apiRoutes = require('./routes/api');

const app = express();

app.use(session({
  secret: crypto.randomBytes(64).toString('hex'),
  resave: false,
  saveUninitialized: true,
  cookie: { secure: false }
}));

app.use(bodyParser.json());
app.use(express.urlencoded({ extended: true }));
app.set('view engine', 'twig');
app.set('views', path.join(__dirname, '/views'));

app.use('/', pageRoutes);
app.use('/api', apiRoutes);
app.get('/uploads', function (req, res) {
  const filename = req.query.file;
  if (filename) {
      res.sendFile(path.resolve(__dirname, 'uploads', filename));
  } else {
      res.status(400).send('Missing file parameter');
  }
});

app.listen(8080, () => {
  console.log('Server is running at http://localhost:8080');
});
