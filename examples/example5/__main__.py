# Example to reproduce https://github.com/juanlao7/codeclose/issues/5

class EmptyClass:
    def __init__(self):
        pass

thisMustBeObfuscated = EmptyClass()
thisMustBeObfuscated.attributesKept = EmptyClass()
thisMustBeObfuscated.attributesKept.thisAttributeMustNotBeObfuscated = 5
