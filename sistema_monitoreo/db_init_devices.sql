-- Registrar 3 máquinas virtuales Ubuntu como dispositivos del admin (usuario_id=1)
-- Las IPs se asignan dinámicamente por Docker, usamos nombres de host como IP temporal
-- que el agente actualizará al enviar métricas

INSERT INTO dispositivos (usuario_id, nombre, ip, tipo, ubicacion, estado)
SELECT 1, 'Ubuntu-VM-01', '172.28.0.10', 'Servidor Linux', 'Docker - VM 1', 'activo'
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM dispositivos WHERE nombre = 'Ubuntu-VM-01' AND usuario_id = 1);

INSERT INTO dispositivos (usuario_id, nombre, ip, tipo, ubicacion, estado)
SELECT 1, 'Ubuntu-VM-02', '172.28.0.11', 'Servidor Linux', 'Docker - VM 2', 'activo'
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM dispositivos WHERE nombre = 'Ubuntu-VM-02' AND usuario_id = 1);

INSERT INTO dispositivos (usuario_id, nombre, ip, tipo, ubicacion, estado)
SELECT 1, 'Ubuntu-VM-03', '172.28.0.12', 'Servidor Linux', 'Docker - VM 3', 'activo'
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM dispositivos WHERE nombre = 'Ubuntu-VM-03' AND usuario_id = 1);
