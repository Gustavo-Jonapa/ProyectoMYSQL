from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
from parser import analyze_sql
import re

app = Flask(__name__)
CORS(app)

MYSQL_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'proyecto58710',
    'port': 3306
}

current_database = None

def get_connection(database=None):
    """Crea conexión a MySQL"""
    try:
        config = MYSQL_CONFIG.copy()
        if database:
            config['database'] = database
        
        connection = mysql.connector.connect(**config)
        return connection
    except Error as e:
        raise Exception(f"No se encontró la base de datos especificada")

def execute_query(query, database=None):
    """Ejecuta una consulta SQL"""
    connection = None
    try:
        connection = get_connection(database)
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute(query)
        
        if query.strip().upper().startswith('SELECT'):
            results = cursor.fetchall()
            return {
                'success': True,
                'data': results,
                'message': f'{len(results)} registros encontrados'
            }
        
        connection.commit()
        affected_rows = cursor.rowcount
        
        return {
            'success': True,
            'affected_rows': affected_rows,
            'message': f'Comando ejecutado correctamente. Filas afectadas: {affected_rows}'
        }
        
    except Error as e:
        return {
            'success': False,
            'error': str(e),
            'message': f'Error MySQL: {str(e)}'
        }
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/api/analyze', methods=['POST'])
def analyze_command():
    """
    Analiza léxica y sintácticamente un comando SQL
    """
    data = request.json
    sql_command = data.get('query', '')
    
    if not sql_command:
        return jsonify({
            'error': 'No se proporcionó ningún comando'
        }), 400
    
    try:
        analysis = analyze_sql(sql_command)
        return jsonify(analysis)
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/api/execute', methods=['POST'])
def execute_command():
    """
    Ejecuta un comando SQL después de validarlo
    """
    global current_database
    
    data = request.json
    sql_command = data.get('query', '').strip()
    
    if not sql_command:
        return jsonify({
            'success': False,
            'error': 'No se proporcionó ningún comando'
        }), 400
    
    try:
        # Primero analizar el comando
        analysis = analyze_sql(sql_command)
        
        # Si hay errores sintácticos, no ejecutar
        if not analysis['syntactic']['valid']:
            return jsonify({
                'success': False,
                'error': 'Error sintáctico',
                'analysis': analysis,
                'message': analysis['syntactic']['message']
            })
        
        # Detectar si es un comando USE para actualizar la base de datos actual
        if sql_command.upper().startswith('USE'):
            match = re.search(r'USE\s+(\w+)', sql_command, re.IGNORECASE)
            if match:
                current_database = match.group(1)
        
        # Detectar DROP DATABASE para limpiar la base de datos actual
        if sql_command.upper().startswith('DROP DATABASE'):
            match = re.search(r'DROP\s+DATABASE\s+(\w+)', sql_command, re.IGNORECASE)
            if match:
                dropped_db = match.group(1)
                # Si se elimina la base de datos actual, limpiarla
                if current_database and current_database.upper() == dropped_db.upper():
                    current_database = None
        
        # Ejecutar el comando
        result = execute_query(sql_command, current_database)
        
        # Agregar análisis al resultado
        result['analysis'] = analysis
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/api/autocomplete', methods=['POST'])
def autocomplete():
    """
    Proporciona sugerencias de autocompletado para comandos SQL
    """
    data = request.json
    partial_query = data.get('query', '').upper()
    
    # Palabras clave de MySQL
    keywords = [
        'CREATE DATABASE', 'CREATE TABLE', 'USE', 
        'INSERT INTO', 'VALUES', 'UPDATE', 'SET', 
        'DELETE FROM', 'DROP DATABASE', 'DROP TABLE',
        'SELECT', 'SELECT * FROM', 'FROM', 'WHERE',
        'INT', 'VARCHAR', 'TEXT', 'DATE', 'FLOAT',
        'PRIMARY KEY', 'NOT NULL', 'AUTO_INCREMENT'
    ]
    
    # Filtrar sugerencias que coincidan
    suggestions = [kw for kw in keywords if kw.startswith(partial_query)]
    
    return jsonify({
        'suggestions': suggestions[:5]  # Máximo 5 sugerencias
    })

@app.route('/api/databases', methods=['GET'])
def list_databases():
    """
    Lista todas las bases de datos disponibles
    """
    try:
        result = execute_query("SHOW DATABASES")
        if result['success']:
            databases = [db['Database'] for db in result['data']]
            return jsonify({
                'success': True,
                'databases': databases
            })
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/tables', methods=['GET'])
def list_tables():
    """
    Lista todas las tablas de la base de datos actual
    """
    global current_database
    
    if not current_database:
        return jsonify({
            'success': False,
            'error': 'No hay una base de datos seleccionada'
        }), 400
    
    try:
        result = execute_query(f"SHOW TABLES", current_database)
        if result['success']:
            table_key = f'Tables_in_{current_database}'
            tables = [table.get(table_key) for table in result['data']]
            return jsonify({
                'success': True,
                'tables': tables
            })
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Verifica el estado del servidor y la conexión a MySQL
    """
    try:
        connection = get_connection()
        connection.close()
        return jsonify({
            'status': 'ok',
            'mysql': 'connected',
            'current_database': current_database
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'mysql': 'disconnected',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
