import mysql.connector
from config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME

def setup_database():
    try:
        # Conectar sin especificar base de datos
        conexion = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = conexion.cursor()

        # Crear base de datos si no existe
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        cursor.execute(f"USE {DB_NAME}")

        # Leer y ejecutar el archivo SQL
        with open('database_setup.sql', 'r', encoding='utf-8') as file:
            sql_script = file.read()

        # Ejecutar cada statement
        statements = sql_script.split(';')
        for statement in statements:
            statement = statement.strip()
            if statement and not statement.startswith('--'):
                try:
                    cursor.execute(statement)
                    print(f"Ejecutado: {statement[:50]}...")
                except Exception as e:
                    print(f"Error en statement: {e}")

        # Agregar nuevas columnas a tablas existentes si no existen
        alter_statements = [
            "ALTER TABLE metricas ADD COLUMN IF NOT EXISTS net_bytes_sent BIGINT DEFAULT 0",
            "ALTER TABLE metricas ADD COLUMN IF NOT EXISTS net_bytes_recv BIGINT DEFAULT 0",
            "ALTER TABLE metricas ADD COLUMN IF NOT EXISTS temperatura DECIMAL(5,2) DEFAULT NULL",
            "ALTER TABLE metricas ADD COLUMN IF NOT EXISTS procesos_activos INT DEFAULT 0",
            "ALTER TABLE metricas ADD COLUMN IF NOT EXISTS uptime BIGINT DEFAULT 0",
            "ALTER TABLE usuarios MODIFY COLUMN rol ENUM('admin', 'user') DEFAULT 'user'"
        ]

        for statement in alter_statements:
            try:
                cursor.execute(statement)
                print(f"Actualización aplicada: {statement}")
            except Exception as e:
                print(f"Error en actualización: {e}")

        # Crear usuario administrador por defecto si no existe
        try:
            cursor.execute("SELECT id FROM usuarios WHERE username = 'jbohorquez'")
            if not cursor.fetchone():
                from werkzeug.security import generate_password_hash
                contraseña_hash = generate_password_hash('admin123')  # Cambiar en producción
                cursor.execute("""
                    INSERT INTO usuarios(username, correo, nombre, contraseña, rol, activo)
                    VALUES(%s, %s, %s, %s, 'admin', TRUE)
                """, ('jbohorquez', 'jbohorquez@admin.com', 'Administrador', contraseña_hash))
                print("Usuario administrador 'jbohorquez' creado con contraseña 'admin123'")
            else:
                print("Usuario administrador 'jbohorquez' ya existe")
        except Exception as e:
            print(f"Error creando usuario administrador: {e}")

        conexion.commit()
        print("Base de datos configurada y actualizada exitosamente!")

    except Exception as e:
        print(f"Error configurando base de datos: {e}")
    finally:
        if 'conexion' in locals():
            conexion.close()

if __name__ == "__main__":
    setup_database()