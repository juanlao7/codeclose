from codeclose.runtime import validate

def computeFibonacci(n):
    validate()
    a, b = 0, 1

    for _ in range(n):
        yield a
        a, b = b, a + b
