import ast
import astunparse
import random
import keyword
import builtins

KEYWORDS = dir(builtins) + keyword.kwlist

MODE_NORMAL = 'normal'
MODE_LIGHT = 'light'

class Analyzer(ast.NodeVisitor):
    def __init__(self):
        self.definedIdentifiers = set()
        self.externalImportedIdentifiers = set()
    
    def analyze(self, content):
        tree = ast.parse(content)
        self.visit(tree)

    def visit_Name(self, node):
        self.generic_visit(node)
        
        if isinstance(node.ctx, ast.Store):
            self.definedIdentifiers.add(node.id)
    
    def visit_Global(self, node):
        self.generic_visit(node)
        
        for name in node.names:
            self.definedIdentifiers.add(name)
        
    def visit_Nonlocal(self, node):
        self.generic_visit(node)
        
        for name in node.names:
            self.definedIdentifiers.add(name)
    
    def visit_Attribute(self, node):
        self.generic_visit(node)
        
        if isinstance(node.ctx, ast.Store):
            self.definedIdentifiers.add(node.attr)

    def visit_arg(self, node):
        self.generic_visit(node)
        self.definedIdentifiers.add(node.arg)
            
    def visit_FunctionDef(self, node):
        self.generic_visit(node)
        self.definedIdentifiers.add(node.name)
    
    def visit_ClassDef(self, node):
        self.generic_visit(node)
        self.definedIdentifiers.add(node.name)
    
    def visit_ImportFrom(self, node):
        # We do not visit the children, on purpose.

        for aliasNode in node.names:
            identifier = aliasNode.asname if aliasNode.asname is not None else aliasNode.name
            
            if node.level == 0:
                # External import.
                self.externalImportedIdentifiers.add(identifier)

    def visit_alias(self, node):
        # Import without a "from" (so it is an external import).
        self.generic_visit(node)
        identifier = node.asname if node.asname is not None else node.name
        self.externalImportedIdentifiers.add(identifier)
    
    def visit_ExceptHandler(self, node):
        self.generic_visit(node)

        if node.name is not None:
            self.definedIdentifiers.add(node.name)

class Obfuscator(ast.NodeTransformer):
    def __init__(self, analyzer, keepIdentifiers=[], keepAttributes=[], mode=MODE_NORMAL):
        self.usedNames = set(KEYWORDS)
        self.randomNameParts = 3 if len(analyzer.definedIdentifiers) > len(KEYWORDS) ** 2 / 2 else 2
        self.mode = mode
        self.keepIdentifiers = set(keepIdentifiers)

        self.identifiersDictionary = self._generateDictionary(analyzer.definedIdentifiers)
        externalImportedIdentifiersDictionary = self._generateDictionary(analyzer.externalImportedIdentifiers)
        self.identifiersDictionary.update(externalImportedIdentifiersDictionary)

        self.keepAttributes = set(keepAttributes).union(externalImportedIdentifiersDictionary.values())

    def obfuscate(self, content):
        tree = ast.parse(content)
        self.visit(tree)
        ast.fix_missing_locations(tree)
        obfuscatedContent = astunparse.unparse(tree)
        obfuscatedContent = obfuscatedContent.replace('\r', '').replace('\n\n', '\n').replace('    ', ' ')
        return obfuscatedContent
    
    def _generateDictionary(self, names):
        dictionary = {}

        for name in names:
            if name in self.keepIdentifiers:
                continue

            if name.startswith('__') and name.endswith('__'):
                continue

            dictionary[name] = self._randomName(name)
        
        return dictionary
    
    def _randomName(self, name):
        if self.mode == MODE_LIGHT:
            obfuscatedName = '%s_%s' % (name, random.randint(9999, 99999))
        else:
            obfuscatedName = '_'.join([random.choice(KEYWORDS).replace('_', '') for i in range(self.randomNameParts)])
        
        numberOfInitialUnderscores = max(0, self._countInitialUnderscores(name) - self._countInitialUnderscores(obfuscatedName))
        numberOfFinalUnderscores = max(0, self._countInitialUnderscores(name[::-1]) - self._countInitialUnderscores(obfuscatedName[::-1]))
        obfuscatedName = '_' * numberOfInitialUnderscores + obfuscatedName + '_' * numberOfFinalUnderscores
        
        if obfuscatedName in self.usedNames:
            return self._randomName(name)
        
        self.usedNames.add(obfuscatedName)
        return obfuscatedName
    
    def _countInitialUnderscores(self, value):
        numberOfInitialUnderscores = 0

        for character in value:
            if character != '_':
                break

            numberOfInitialUnderscores += 1
        
        return numberOfInitialUnderscores
    
    def visit_Name(self, node):
        self.generic_visit(node)
        
        if node.id in self.identifiersDictionary:
            node.id = self.identifiersDictionary[node.id]
        
        return node
    
    def visit_Global(self, node):
        self.generic_visit(node)
        
        for i in range(len(node.names)):
            if node.names[i] in self.identifiersDictionary:
                node.names[i] = self.identifiersDictionary[node.names[i]]

        return node
        
    def visit_Nonlocal(self, node):
        self.generic_visit(node)
        
        for i in range(len(node.names)):
            if node.names[i] in self.identifiersDictionary:
                node.names[i] = self.identifiersDictionary[node.names[i]]

        return node
    
    def visit_Attribute(self, node):
        self.generic_visit(node)
        originalIdentifier = node.value

        while not isinstance(originalIdentifier, ast.Name):
            if isinstance(originalIdentifier, ast.Attribute) or isinstance(originalIdentifier, ast.Subscript):
                originalIdentifier = originalIdentifier.value
            elif isinstance(originalIdentifier, ast.Call):
                originalIdentifier = originalIdentifier.func
            else:
                originalIdentifier = None
                break

        if originalIdentifier is None or originalIdentifier.id in self.keepAttributes:
            return node
        
        if node.attr in self.identifiersDictionary:
            node.attr = self.identifiersDictionary[node.attr]
        
        return node
    
    def visit_arg(self, node):
        self.generic_visit(node)
        
        if node.arg in self.identifiersDictionary:
            node.arg = self.identifiersDictionary[node.arg]
        
        return node
    
    def visit_FunctionDef(self, node):
        self.generic_visit(node)
        
        if node.name in self.identifiersDictionary:
            node.name = self.identifiersDictionary[node.name]
        
        return node

    def visit_ClassDef(self, node):
        self.generic_visit(node)
        
        if node.name in self.identifiersDictionary:
            node.name = self.identifiersDictionary[node.name]
        
        return node
        
    def visit_Str(self, node):
        self.generic_visit(node)

        if not node.s or self.mode == MODE_LIGHT:
            return node
    
        stringBytes = node.s.encode('utf-8')
        intValue = int.from_bytes(stringBytes, 'big')
        intValueSize = (intValue.bit_length() + 7) // 8
        intValuePart1 = random.randint(1, intValue - 1)
        intValuePart2 = intValue - intValuePart1
        
        # (${intValuePart1} + int(${intValuePart2})).to_bytes(${intValueSize}, 'big').decode()
        return ast.Call(func=ast.Attribute(value=ast.Call(func=ast.Attribute(value=ast.BinOp(left=ast.Num(n=intValuePart1), op=ast.Add(), right=ast.Call(func=ast.Name(id='int', ctx=ast.Load()), args=[ast.Num(n=intValuePart2)], keywords=[])), attr='to_bytes', ctx=ast.Load()), args=[ast.Num(n=intValueSize), ast.Str(s='big')], keywords=[]), attr='decode', ctx=ast.Load()), args=[], keywords=[])
    
    def visit_ImportFrom(self, node):
        if node.level == 0:
            self.generic_visit(node)
            return node
        
        for aliasNode in node.names:
            if aliasNode.name in self.identifiersDictionary:
                aliasNode.name = self.identifiersDictionary[aliasNode.name]
        
        return node
    
    def visit_alias(self, node):
        # Import without a "from" (so it is an external import).
        self.generic_visit(node)
        identifier = node.asname if node.asname is not None else node.name
        
        if identifier in self.identifiersDictionary:
            node.asname = self.identifiersDictionary[identifier]
        
        return node

    def visit_ExceptHandler(self, node):
        self.generic_visit(node)

        if node.name is None:
            if node.type is not None:
                node.name = self._randomName(node.name)
        elif node.name in self.identifiersDictionary:
            node.name = self.identifiersDictionary[node.name]
        
        return node
