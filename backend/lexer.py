import re
from enum import Enum

class TokenType(Enum):
    CREATE = "CREATE"
    DATABASE = "DATABASE"
    TABLE = "TABLE"
    USE = "USE"
    INSERT = "INSERT"
    INTO = "INTO"
    VALUES = "VALUES"
    UPDATE = "UPDATE"
    SET = "SET"
    DELETE = "DELETE"
    FROM = "FROM"
    WHERE = "WHERE"
    
    INT = "INT"
    VARCHAR = "VARCHAR"
    TEXT = "TEXT"
    DATE = "DATE"
    FLOAT = "FLOAT"
    BOOLEAN = "BOOLEAN"
    
    LPAREN = "("
    RPAREN = ")"
    COMMA = ","
    SEMICOLON = ";"
    EQUALS = "="
    ASTERISK = "*"
    
    IDENTIFIER = "IDENTIFIER"
    STRING = "STRING"
    NUMBER = "NUMBER"
    
    WHITESPACE = "WHITESPACE"
    UNKNOWN = "UNKNOWN"
    EOF = "EOF"

class Token:
    def __init__(self, type, value, position):
        self.type = type
        self.value = value
        self.position = position
    
    def __repr__(self):
        return f"Token({self.type}, {repr(self.value)}, pos={self.position})"

class Lexer:
    def __init__(self, text):
        self.text = text.upper()
        self.original_text = text
        self.position = 0
        self.tokens = []
        
        self.keywords = {
            'CREATE', 'DATABASE', 'TABLE', 'USE', 'INSERT', 'INTO',
            'VALUES', 'UPDATE', 'SET', 'DELETE', 'FROM', 'WHERE',
            'INT', 'VARCHAR', 'TEXT', 'DATE', 'FLOAT', 'BOOLEAN',
            'PRIMARY', 'KEY', 'NOT', 'NULL', 'AUTO_INCREMENT'
        }
    
    def current_char(self):
        if self.position >= len(self.text):
            return None
        return self.text[self.position]
    
    def peek_char(self, offset=1):
        pos = self.position + offset
        if pos >= len(self.text):
            return None
        return self.text[pos]
    
    def advance(self):
        self.position += 1
    
    def skip_whitespace(self):
        while self.current_char() and self.current_char().isspace():
            self.advance()
    
    def read_string(self):
        quote = self.original_text[self.position]
        start = self.position
        self.advance()
        
        value = ""
        while self.current_char() and self.original_text[self.position] != quote:
            value += self.original_text[self.position]
            self.advance()
        
        if self.current_char():
            self.advance()
        
        return value
    
    def read_number(self):
        start = self.position
        while self.current_char() and (self.current_char().isdigit() or self.current_char() == '.'):
            self.advance()
        return self.text[start:self.position]
    
    def read_identifier(self):
        start = self.position
        while self.current_char() and (self.current_char().isalnum() or self.current_char() == '_'):
            self.advance()
        return self.text[start:self.position]
    
    def tokenize(self):
        self.tokens = []
        
        while self.position < len(self.text):
            self.skip_whitespace()
            
            if self.position >= len(self.text):
                break
            
            char = self.current_char()
            original_char = self.original_text[self.position]
            
            if original_char in ("'", '"'):
                value = self.read_string()
                self.tokens.append(Token(TokenType.STRING, value, self.position))
            
            elif char.isdigit():
                value = self.read_number()
                self.tokens.append(Token(TokenType.NUMBER, value, self.position))
            
            elif char.isalpha() or char == '_':
                value = self.read_identifier()
                if value in self.keywords:
                    token_type = TokenType[value] if hasattr(TokenType, value) else TokenType.IDENTIFIER
                    self.tokens.append(Token(token_type, value, self.position))
                else:
                    self.tokens.append(Token(TokenType.IDENTIFIER, value, self.position))
            
            elif char == '(':
                self.tokens.append(Token(TokenType.LPAREN, char, self.position))
                self.advance()
            elif char == ')':
                self.tokens.append(Token(TokenType.RPAREN, char, self.position))
                self.advance()
            elif char == ',':
                self.tokens.append(Token(TokenType.COMMA, char, self.position))
                self.advance()
            elif char == ';':
                self.tokens.append(Token(TokenType.SEMICOLON, char, self.position))
                self.advance()
            elif char == '=':
                self.tokens.append(Token(TokenType.EQUALS, char, self.position))
                self.advance()
            elif char == '*':
                self.tokens.append(Token(TokenType.ASTERISK, char, self.position))
                self.advance()
            else:
                self.tokens.append(Token(TokenType.UNKNOWN, char, self.position))
                self.advance()
        
        self.tokens.append(Token(TokenType.EOF, None, self.position))
        return self.tokens
    
    def get_tokens_info(self):
        return [
            {
                'type': token.type.value,
                'value': token.value,
                'position': token.position
            }
            for token in self.tokens if token.type != TokenType.EOF
        ] 
