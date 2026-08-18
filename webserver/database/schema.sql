DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS comments;

CREATE TABLE users (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    email    TEXT
);

CREATE TABLE products (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    name     TEXT NOT NULL,
    category TEXT,
    price    REAL,
    img_address TEXT
);

CREATE TABLE comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    username TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);

-- Demo credentials for the lab target: admin / admin
INSERT INTO users (username, password, email) VALUES
    ('admin', 'admin', 'admin@example.com');

INSERT INTO products (id, name, category, price, img_address) VALUES
    (1, 'Keyboard', 'peripherals', 29.99,
     'https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fwww.pcgamesn.com%2Fwp-content%2Fsites%2Fpcgamesn%2F2022%2F10%2Fcorsair-k100-air-review-ultra-thin-wireless-mechanical-keyboard.jpg&f=1&nofb=1&ipt=139b287726db6153ae1bf4804b98ef32dc6fa0c9105bf7821abe5ceb12784bdd'),
    (2, 'Monitor', 'displays', 149.50,
     'https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fm.media-amazon.com%2Fimages%2FI%2F71jYGe-4LES.jpg&f=1&nofb=1&ipt=dff61700f1c98ef0783dc6e70e342395cd7515ddacb2cb1b46b06e1859d557b5'),
    (3, 'Mouse', 'peripherals', 14.99,
     'https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fm.media-amazon.com%2Fimages%2FI%2F61Mk3YqYHpL._AC_SL1500_.jpg&f=1&nofb=1&ipt=77e377381f35dfad292ee16fe4e11c3face3ac1bc42f0502b5ce1fdfb773c5b2'),
    (4, 'Webcam', 'peripherals', 39.00,
     'https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fm.media-amazon.com%2Fimages%2FI%2F71GjDKfOnhL._AC_SL1500_.jpg&f=1&nofb=1&ipt=5fb32cd45fe613e57ae2969461cab2da8d0bd063c970ae1f8b66aa44fe887e12'),
    (5, 'Desk Lamp', 'accessories', 22.49,
     'https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fcdn.homedit.com%2Fwp-content%2Fuploads%2F2016%2F06%2FAmeico-Design-table-lamp-683x1024.jpg&f=1&nofb=1&ipt=b0aa75739511b74208df6c18f3e65079936d39208145f99a0a42937ff2f0e7d8');
