SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS books (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    author VARCHAR(150) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO books (title, author) VALUES
    ('Война и мир', 'Лев Толстой'),
    ('Преступление и наказание', 'Фёдор Достоевский');
