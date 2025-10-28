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
    try:
        config = MYSQL_CONFIG.copy()
        if database:
            config['database'] = database
        
        connection = mysql.connector.connect(**config)
        return connection
    except Error as e:
        raise Exception(f"No se encontró la base de datos especificada")

def execute_query(query, database=None):
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
    global current_database
    
    data = request.json
    sql_command = data.get('query', '').strip()
    
    if not sql_command:
        return jsonify({
            'success': False,
            'error': 'No se proporcionó ningún comando'
        }), 400
    
    try:
        analysis = analyze_sql(sql_command)
        
        if not analysis['syntactic']['valid']:
            return jsonify({
                'success': False,
                'error': 'Error sintáctico',
                'analysis': analysis,
                'message': analysis['syntactic']['message']
            })
        
        if sql_command.upper().startswith('USE'):
            match = re.search(r'USE\s+(\w+)', sql_command, re.IGNORECASE)
            if match:
                current_database = match.group(1)
        
        result = execute_query(sql_command, current_database)
        
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
    data = request.json
    partial_query = data.get('query', '').upper()
    
    keywords = [
        'CREATE DATABASE', 'CREATE TABLE', 'USE', 
        'INSERT INTO', 'VALUES', 'UPDATE', 'SET', 
        'DELETE FROM', 'WHERE', 'SELECT', 'FROM',
        'INT', 'VARCHAR', 'TEXT', 'DATE', 'FLOAT',
        'PRIMARY KEY', 'NOT NULL', 'AUTO_INCREMENT'
    ]
    
    suggestions = [kw for kw in keywords if kw.startswith(partial_query)]
    
    return jsonify({
        'suggestions': suggestions[:5]  # Máximo 5 sugerencias
    })

@app.route('/api/databases', methods=['GET'])
def list_databases():
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