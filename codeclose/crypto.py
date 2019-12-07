from Cryptodome.PublicKey import RSA
from Cryptodome.Math.Numbers import Integer
from Cryptodome.Math.Primality import test_probable_prime
from Cryptodome import Random

COMPOSITE = 0

def generateProbablePrime(**kwargs):
    """Modified version of pycryptodome's Cryptodome.Math.Primality.generate_probable_prime to create primes of any size."""

    exact_bits = kwargs.pop("exact_bits", None)
    randfunc = kwargs.pop("randfunc", None)
    prime_filter = kwargs.pop("prime_filter", lambda x: True)
    if kwargs:
        raise ValueError("Unknown parameters: " + kwargs.keys())

    if exact_bits is None:
        raise ValueError("Missing exact_bits parameter")

    if randfunc is None:
        randfunc = Random.new().read

    result = COMPOSITE
    while result == COMPOSITE:
        candidate = Integer.random(exact_bits=exact_bits,
                                   randfunc=randfunc) | 1
        if not prime_filter(candidate):
            continue
        result = test_probable_prime(candidate, randfunc)
    return candidate

def generateRSAKey(bits, randfunc=None, e=65537):
    """Modified version of pycryptodome's Crypto.RSA.generate to allow keys of any size."""

    if e % 2 == 0 or e < 3:
        raise ValueError("RSA public exponent must be a positive, odd integer larger than 2.")

    if randfunc is None:
        randfunc = Random.get_random_bytes

    d = n = Integer(1)
    e = Integer(e)

    while n.size_in_bits() != bits and d < (1 << (bits // 2)):
        # Generate the prime factors of n: p and q.
        # By construciton, their product is always
        # 2^{bits-1} < p*q < 2^bits.
        size_q = bits // 2
        size_p = bits - size_q

        min_p = min_q = (Integer(1) << (2 * size_q - 1)).sqrt()
        if size_q != size_p:
            min_p = (Integer(1) << (2 * size_p - 1)).sqrt()

        def filter_p(candidate):
            return candidate > min_p and (candidate - 1).gcd(e) == 1

        p = generateProbablePrime(exact_bits=size_p,
                                    randfunc=randfunc,
                                    prime_filter=filter_p)

        min_distance = Integer(1) << max(0, bits // 2 - 100)

        def filter_q(candidate):
            return (candidate > min_q and
                    (candidate - 1).gcd(e) == 1 and
                    abs(candidate - p) > min_distance)

        q = generateProbablePrime(exact_bits=size_q,
                                    randfunc=randfunc,
                                    prime_filter=filter_q)

        n = p * q
        lcm = (p - 1).lcm(q - 1)
        d = e.inverse(lcm)

    if p > q:
        p, q = q, p

    u = p.inverse(q)

    return RSA.RsaKey(n=n, e=e, d=d, p=p, q=q, u=u)

def adaptForAES(data):
    dataLength = len(data)
    return data.ljust(dataLength + (16 - dataLength) % 16, b'\0')
