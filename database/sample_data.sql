INSERT INTO categories (name) VALUES
('Laptops'), ('Mobiles'), ('Audio'), ('Wearables'), ('Accessories'), ('Bags');

INSERT INTO products (category_id, name, description, price, stock, image_url, is_featured) VALUES
(1, 'UltraBook Pro 14',      '14-inch laptop, Intel i5, 16GB RAM, 512GB SSD. Light and fast for students.', 55999.00, 15, 'laptop.svg', 1),
(1, 'GameForce 15',          '15.6-inch gaming laptop, Ryzen 7, 16GB RAM, RTX graphics.',                  84999.00,  8, 'gaming-laptop.svg', 0),
(2, 'Nova X Smartphone',     '6.5-inch AMOLED display, 128GB storage, 50MP camera, 5000mAh battery.',      19999.00, 40, 'smartphone.svg', 1),
(2, 'Nova Lite 5G',          '5G phone with 6GB RAM and a smooth 90Hz display.',                           12999.00, 55, 'smartphone-lite.svg', 0),
(3, 'BassBoost Headphones',  'Wireless over-ear headphones with noise cancellation, 30h battery.',          3499.00, 60, 'headphones.svg', 1),
(3, 'PocketBeats Earbuds',   'True wireless earbuds with charging case.',                                   1999.00, 80, 'earbuds.svg', 0),
(4, 'FitTime Smart Watch',   'Heart-rate, sleep tracking, 7-day battery, water resistant.',                 2999.00, 35, 'smartwatch.svg', 1),
(4, 'FitBand Mini',          'Slim fitness band with step counter and notifications.',                      1499.00, 70, 'fitband.svg', 0),
(5, 'MechType Keyboard',     'RGB mechanical keyboard with blue switches.',                                 2499.00, 45, 'keyboard.svg', 1),
(5, 'GlideX Wireless Mouse', 'Ergonomic 2.4GHz wireless mouse, silent clicks.',                              699.00, 100, 'mouse.svg', 0),
(5, 'USB-C Hub 7-in-1',      'HDMI, USB 3.0, SD card reader and USB-C charging.',                          1799.00, 50, 'usb-hub.svg', 0),
(6, 'TrailPack Backpack',    '30L laptop backpack, water resistant, padded straps.',                        1299.00, 65, 'backpack.svg', 1)
