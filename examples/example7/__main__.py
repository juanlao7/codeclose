# Example to reproduce https://github.com/juanlao7/codeclose/issues/1#issuecomment-784574653
obfuscatedIdentifier = {'name': 'value'}
attributesKept = obfuscatedIdentifier.copy()

attributesKept = ['one', 'two']
attributesKept.sort()
