-- Inserta usuario administrador si no existe
INSERT INTO usuarios (username, correo, contraseña, nombre, rol, activo)
SELECT 'jbohorquez', 'jbohorquez@example.com', 'pbkdf2:sha256:600000$P3Wkc1pyIv4V09JE$d50644efcde31a7ca506f32bbd96dc490565152f46e6f563b938fdd57b5d3d21', 'Juan Bohorquez', 'admin', 1
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM usuarios WHERE username = 'jbohorquez');
