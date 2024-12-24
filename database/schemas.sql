CREATE DATABASE IF NOT EXISTS chatify;
USE chatify;

CREATE TABLE IF NOT EXISTS user
(
	id INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(30) NOT NULL UNIQUE,
    hash VARCHAR(162) NOT NULL,
    pfp_filename VARCHAR(75) NOT NULL DEFAULT "default_pfp.jpeg",
    name VARCHAR(50),
    bio VARCHAR(256),
    is_online TINYINT
);

CREATE TABLE IF NOT EXISTS friendships
(
	id INT PRIMARY KEY AUTO_INCREMENT,
    low_friend_id INT NOT NULL REFERENCES user(id),
    high_friend_id INT NOT NULL REFERENCES user(id),
    CHECK (low_friend_id < high_friend_id)
);

CREATE TABLE IF NOT EXISTS friend_requests
(
	id INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
	req_from INT NOT NULL UNIQUE,
    req_to INT NOT NULL UNIQUE,
    FOREIGN KEY (req_from) REFERENCES user(id),
	FOREIGN KEY (req_to) REFERENCES user(id)
);

CREATE TABLE IF NOT EXISTS messages
(
	id INT PRIMARY KEY AUTO_INCREMENT,
    msg_from INT NOT NULL,
    msg_to INT NOT NULL,
    msg VARCHAR(5000) NOT NULL,
    timestamp CHAR(20) NOT NULL,
    FOREIGN KEY (msg_from) REFERENCES user(id),
    FOREIGN KEY (msg_to) REFERENCES user(id)
);