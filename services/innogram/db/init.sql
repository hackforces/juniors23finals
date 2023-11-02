CREATE TABLE IF NOT EXISTS users (
  id SERIAL PRIMARY KEY,
  username VARCHAR(50) UNIQUE NOT NULL,
  password VARCHAR(80) NOT NULL,
  subscribed_to INTEGER[]
);

CREATE TABLE IF NOT EXISTS posts (
  uid SERIAL PRIMARY KEY,
  post_id SERIAL,
  owner_id INTEGER REFERENCES users(id),
  owner_username VARCHAR(50) REFERENCES users(username),
  private BOOLEAN NOT NULL,
  image VARCHAR(255) NOT NULL,
  description TEXT,
  likes INTEGER[]
);

CREATE TABLE IF NOT EXISTS comments (
  id SERIAL PRIMARY KEY,
  post_uid INTEGER REFERENCES posts(uid),
  user_id INTEGER REFERENCES users(id),
  username VARCHAR(50) REFERENCES users(username),
  comment TEXT
);

CREATE OR REPLACE FUNCTION calculate_postId()
RETURNS TRIGGER AS $$
BEGIN
  NEW.post_id := (SELECT COALESCE(MAX(post_id), 0) + 1 FROM posts WHERE owner_id = NEW.owner_id);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER calculate_postId_before_insert
BEFORE INSERT ON posts
FOR EACH ROW
EXECUTE PROCEDURE calculate_postId();
