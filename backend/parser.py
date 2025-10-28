from lexer import Lexer, TokenType

class ParseError(Exception):
    def __init__(self, message, position=None):
        self.message = message
        self.position = position
        super().__init__(self.message)

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current = 0
    
    def current_token(self):
        if self.current < len(self.tokens):
            return self.tokens[self.current]
        return self.tokens[-1]
    
    def peek_token(self, offset=1):
        pos = self.current + offset
        if pos < len(self.tokens):
            return self.tokens[pos]
        return self.tokens[-1]
    
    def advance(self):
        if self.current < len(self.tokens) - 1:
            self.current += 1
    
    def expect(self, token_type):
        token = self.current_token()
        if token.type != token_type:
            raise ParseError(
                f"Comando incompleto",
                token.position
            )
        self.advance()
        return token
    
    def match(self, *token_types):
        return self.current_token().type in token_types
    
    def parse(self):
        try:
            result = self.parse_statement()
            
            if not self.match(TokenType.SEMICOLON, TokenType.EOF):
                raise ParseError(
                    "Se esperaba ';' al final del comando",
                    self.current_token().position
                )
            
            return {
                'valid': True,
                'message': 'Comando SQL válido',
                'statement_type': result
            }
        except ParseError as e:
            return {
                'valid': False,
                'message': e.message,
                'position': e.position
            }
    
    def parse_statement(self):
        token = self.current_token()
        
        if token.type == TokenType.CREATE:
            return self.parse_create()
        elif token.type == TokenType.USE:
            return self.parse_use()
        elif token.type == TokenType.INSERT:
            return self.parse_insert()
        elif token.type == TokenType.UPDATE:
            return self.parse_update()
        elif token.type == TokenType.DELETE:
            return self.parse_delete()
        else:
            raise ParseError(
                f"Comando no reconocido: {token.value}",
                token.position
            )
    
    def parse_create(self):
        self.expect(TokenType.CREATE)
        
        if self.match(TokenType.DATABASE):
            return self.parse_create_database()
        elif self.match(TokenType.TABLE):
            return self.parse_create_table()
        else:
            raise ParseError(
                "Después de CREATE se esperaba DATABASE o TABLE",
                self.current_token().position
            )
    
    def parse_create_database(self):
        self.expect(TokenType.DATABASE)
        self.expect(TokenType.IDENTIFIER)
        return "CREATE_DATABASE"
    
    def parse_create_table(self):
        self.expect(TokenType.TABLE)
        self.expect(TokenType.IDENTIFIER)
        self.expect(TokenType.LPAREN)
        
        self.parse_column_definitions()
        
        self.expect(TokenType.RPAREN)
        return "CREATE_TABLE"
    
    def parse_column_definitions(self):
        while True:
            self.expect(TokenType.IDENTIFIER)
            
            if not self.match(TokenType.INT, TokenType.VARCHAR, TokenType.TEXT, 
                             TokenType.DATE, TokenType.FLOAT, TokenType.BOOLEAN):
                raise ParseError(
                    "Se esperaba un tipo de dato válido (INT, VARCHAR, TEXT, etc.)",
                    self.current_token().position
                )
            self.advance()
            
            if self.tokens[self.current - 1].type == TokenType.VARCHAR:
                if self.match(TokenType.LPAREN):
                    self.advance()
                    self.expect(TokenType.NUMBER)
                    self.expect(TokenType.RPAREN)
            
            while self.match(TokenType.IDENTIFIER):
                self.advance()
            
            if self.match(TokenType.COMMA):
                self.advance()
            else:
                break
    
    def parse_use(self):
        self.expect(TokenType.USE)
        self.expect(TokenType.IDENTIFIER)
        return "USE"
    
    def parse_insert(self):
        self.expect(TokenType.INSERT)
        self.expect(TokenType.INTO)
        self.expect(TokenType.IDENTIFIER)
        
        if self.match(TokenType.LPAREN):
            self.advance()
            self.parse_identifier_list()
            self.expect(TokenType.RPAREN)
        
        self.expect(TokenType.VALUES)
        self.expect(TokenType.LPAREN)
        self.parse_value_list()
        self.expect(TokenType.RPAREN)
        
        return "INSERT"
    
    def parse_update(self):
        self.expect(TokenType.UPDATE)
        self.expect(TokenType.IDENTIFIER)
        self.expect(TokenType.SET)
        
        self.parse_assignments()

        if self.match(TokenType.WHERE):
            self.advance()
            self.parse_condition()
        
        return "UPDATE"
    
    def parse_delete(self):
        self.expect(TokenType.DELETE)
        self.expect(TokenType.FROM)
        self.expect(TokenType.IDENTIFIER)
        
        if self.match(TokenType.WHERE):
            self.advance()
            self.parse_condition()
        
        return "DELETE"
    
    def parse_identifier_list(self):
        self.expect(TokenType.IDENTIFIER)
        while self.match(TokenType.COMMA):
            self.advance()
            self.expect(TokenType.IDENTIFIER)
    
    def parse_value_list(self):
        self.parse_value()
        while self.match(TokenType.COMMA):
            self.advance()
            self.parse_value()
    
    def parse_value(self):
        if self.match(TokenType.STRING, TokenType.NUMBER, TokenType.IDENTIFIER):
            self.advance()
        else:
            raise ParseError(
                "Se esperaba un valor (string, número o identificador)",
                self.current_token().position
            )
    
    def parse_assignments(self):
        self.expect(TokenType.IDENTIFIER)
        self.expect(TokenType.EQUALS)
        self.parse_value()
        
        while self.match(TokenType.COMMA):
            self.advance()
            self.expect(TokenType.IDENTIFIER)
            self.expect(TokenType.EQUALS)
            self.parse_value()
    
    def parse_condition(self):
        self.expect(TokenType.IDENTIFIER)
        self.expect(TokenType.EQUALS)
        self.parse_value()


def analyze_sql(sql_command):
    lexer = Lexer(sql_command)
    tokens = lexer.tokenize()
    
    parser = Parser(tokens)
    parse_result = parser.parse()
    
    return {
        'lexical': {
            'tokens': lexer.get_tokens_info(),
            'token_count': len(tokens) - 1
        },
        'syntactic': parse_result
    }
