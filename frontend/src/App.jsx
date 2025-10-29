import { useState, useEffect, useRef } from 'react';
import './App.css';

export default function MySQLInterface() {
  const [query, setQuery] = useState('');
  const [result, setResult] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [loading, setLoading] = useState(false);
  const [databases, setDatabases] = useState([]);
  const [currentDb, setCurrentDb] = useState(null);
  const textareaRef = useRef(null);

  const API_URL = 'http://localhost:5000/api';
  
  const templates = {
    createDb: 'CREATE DATABASE mi_base_datos;',
    use: 'USE mi_base_datos;',
    createTable: `CREATE TABLE usuarios (
  id INT PRIMARY KEY AUTO_INCREMENT,
  nombre VARCHAR(100) NOT NULL,
  email VARCHAR(100),
  fecha_registro DATE
);`,
    insert: "INSERT INTO usuarios (nombre, email, fecha_registro) VALUES ('Juan Pérez', 'juan@email.com', '2025-10-26');",
    update: "UPDATE usuarios SET email = 'nuevo@email.com' WHERE id = 1;",
    delete: "DELETE FROM usuarios WHERE id = 1;"
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      if (query.trim()) {
        fetchSuggestions();
      } else {
        setSuggestions([]);
        setShowSuggestions(false);
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [query]);

  useEffect(() => {
    fetchDatabases();
    checkHealth();
  }, []);

  const fetchSuggestions = async () => {
    try {
      const response = await fetch(`${API_URL}/autocomplete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: query.trim() })
      });
      const data = await response.json();
      if (data.suggestions && data.suggestions.length > 0) {
        setSuggestions(data.suggestions);
        setShowSuggestions(true);
      } else {
        setShowSuggestions(false);
      }
    } catch (error) {
      console.error('Error obteniendo sugerencias:', error);
    }
  };

  const fetchDatabases = async () => {
    try {
      const response = await fetch(`${API_URL}/databases`);
      const data = await response.json();
      if (data.success) {
        setDatabases(data.databases);
      }
    } catch (error) {
      console.error('Error obteniendo bases de datos:', error);
    }
  };

  const checkHealth = async () => {
    try {
      const response = await fetch(`${API_URL}/health`);
      const data = await response.json();
      if (data.current_database) {
        setCurrentDb(data.current_database);
      }
    } catch (error) {
      console.error('Error verificando estado:', error);
    }
  };

  const analyzeQuery = async () => {
    if (!query.trim()) return;
    try {
      const response = await fetch(`${API_URL}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      });
      const data = await response.json();
      setAnalysis(data);
    } catch (error) {
      console.error('Error analizando:', error);
      setAnalysis({ error: error.message });
    }
  };

  const executeQuery = async () => {
    if (!query.trim()) {
      alert('Por favor ingresa un comando SQL');
      return;
    }

    setLoading(true);
    setResult(null);
    setAnalysis(null);

    try {
      const response = await fetch(`${API_URL}/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      });
      
      const data = await response.json();
      setResult(data);
      
      if (data.analysis) {
        setAnalysis(data.analysis);
      }

      if (query.toUpperCase().includes('CREATE DATABASE')) {
        fetchDatabases();
      }

      if (query.toUpperCase().includes('DROP DATABASE')) {
        fetchDatabases();
        checkHealth(); // Actualizar el estado de la base de datos activa
      }

      if (query.toUpperCase().startsWith('USE')) {
        checkHealth();
      }
    } catch (error) {
      setResult({
        success: false,
        error: error.message,
        message: `Error de conexión: ${error.message}`
      });
    } finally {
      setLoading(false);
    }
  };

  const applySuggestion = (suggestion) => {
    setQuery(suggestion + ' ');
    setShowSuggestions(false);
    textareaRef.current?.focus();
  };

  const loadTemplate = (templateKey) => {
    setQuery(templates[templateKey]);
    setShowSuggestions(false);
  };

  return (
    <div className="app-container">
      <div className="content-wrapper">
        {/* Header */}
        <div className="header-card">
          <div className="header-content">
            <div>
              <h1 className="title">Bases de datos MySQL</h1>
            </div>
            {currentDb && (
              <div className="current-db">
                <p>Base de datos activa: <strong>{currentDb}</strong></p>
              </div>
            )}
          </div>
        </div>

        <div className="main-grid">
          {/* Panel Principal */}
          <div className="main-panel">
            {/* Plantillas */}
            <div className="card">
              <h2 className="card-title">Plantillas Rápidas</h2>
              <div className="templates-grid">
                <button onClick={() => loadTemplate('createDb')} className="btn btn-purple">
                  CREATE DATABASE
                </button>
                <button onClick={() => loadTemplate('use')} className="btn btn-blue">
                  USE
                </button>
                <button onClick={() => loadTemplate('createTable')} className="btn btn-green">
                  CREATE TABLE
                </button>
                <button onClick={() => loadTemplate('insert')} className="btn btn-yellow">
                  INSERT
                </button>
                <button onClick={() => loadTemplate('update')} className="btn btn-orange">
                  UPDATE
                </button>
                <button onClick={() => loadTemplate('delete')} className="btn btn-red">
                  DELETE
                </button>
              </div>
            </div>

            {/* Editor */}
            <div className="card">
              <h2 className="card-title">Editor SQL</h2>
              <div className="editor-container">
                <textarea
                  ref={textareaRef}
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Escribe tu comando SQL aquí..."
                  className="sql-editor"
                  spellCheck={false}
                />
                
                {showSuggestions && suggestions.length > 0 && (
                  <div className="suggestions-box">
                    <div className="suggestions-header">
                      <p>Sugerencias</p>
                    </div>
                    {suggestions.map((suggestion, index) => (
                      <button
                        key={index}
                        onClick={() => applySuggestion(suggestion)}
                        className="suggestion-item"
                      >
                        {suggestion}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              <div className="button-group">
                <button
                  onClick={executeQuery}
                  disabled={loading}
                  className="btn btn-execute"
                >
                  {loading ? 'Ejecutando...' : 'Ejecutar Comando'}
                </button>
                <button onClick={analyzeQuery} className="btn btn-analyze">
                  Analizar
                </button>
                <button
                  onClick={() => {
                    setQuery('');
                    setResult(null);
                    setAnalysis(null);
                  }}
                  className="btn btn-clear"
                >
                  Limpiar
                </button>
              </div>
            </div>

            {/* Resultados */}
            {result && (
              <div className="card">
                <h2 className="card-title">
                  {result.success ? 'Resultado' : 'Error'}
                </h2>
                
                <div className={`result-box ${result.success ? 'success' : 'error'}`}>
                  <p className="result-message">{result.message}</p>

                  {result.data && result.data.length > 0 && (
                    <div className="table-container">
                      <table className="data-table">
                        <thead>
                          <tr>
                            {Object.keys(result.data[0]).map((key) => (
                              <th key={key}>{key}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {result.data.map((row, i) => (
                            <tr key={i}>
                              {Object.values(row).map((value, j) => (
                                <td key={j}>
                                  {value !== null ? String(value) : 'NULL'}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Panel Lateral */}
          <div className="sidebar">
            {/* Análisis Léxico */}
            {analysis?.lexical && (
              <div className="card">
                <h2 className="card-title">Análisis Léxico</h2>
                <div className="analysis-content">
                  <p className="token-count">
                    Tokens encontrados: <strong>{analysis.lexical.token_count}</strong>
                  </p>
                  <div className="tokens-list">
                    {analysis.lexical.tokens.map((token, i) => (
                      <div key={i} className="token-item">
                        <div className="token-header">
                          <span className="token-type">{token.type}</span>
                          <span className="token-pos">pos: {token.position}</span>
                        </div>
                        <p className="token-value">
                          {token.value || '(símbolo)'}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Análisis Sintáctico */}
            {analysis?.syntactic && (
              <div className="card">
                <h2 className="card-title">Análisis Sintáctico</h2>
                <div className={`syntax-result ${analysis.syntactic.valid ? 'valid' : 'invalid'}`}>
                  <div className="syntax-header">
                    <p className="syntax-status">
                      {analysis.syntactic.valid ? 'Sintaxis válida' : 'Error de sintaxis'}
                    </p>
                  </div>
                  <p className="syntax-message">{analysis.syntactic.message}</p>
                  {analysis.syntactic.statement_type && (
                    <p className="syntax-type">
                      Tipo: <strong>{analysis.syntactic.statement_type}</strong>
                    </p>
                  )}
                </div>
              </div>
            )}

            {/* Bases de datos */}
            {databases.length > 0 && (
              <div className="card">
                <h2 className="card-title">Bases de Datos</h2>
                <div className="databases-list">
                  {databases.map((db, i) => (
                    <div
                      key={i}
                      className={`database-item ${db === currentDb ? 'active' : ''}`}
                    >
                      {db === currentDb && <span className="active-indicator">▶</span>}
                      {db}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}