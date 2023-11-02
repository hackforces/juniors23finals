module.exports = function checkAuth(req, res, next) {
    if (req.session.userId) {
        next();
    } else {
        res.redirect("/registration");
    }
  }
  