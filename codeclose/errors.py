class InvalidProductKey(Exception):
    def __init__(self):
        super().__init__('Invalid product key.')

class InvalidProductId(Exception):
    def __init__(self):
        super().__init__('Valid product key, but not for this product.')

class ExpiredLicense(Exception):
    def __init__(self, expirationTime):
        super().__init__('Expired license.')
        self.expirationTime = expirationTime

