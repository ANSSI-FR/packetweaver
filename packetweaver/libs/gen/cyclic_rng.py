import random
import math
import os
import gmpy2


class CyclicPRNG():
    def __init__(self, total):
        # We increase total by one, so that we can generate numbers between 2 and total + 1 with the same probability
        # of appearance anywhere in the generated series of random numbers. This is because the small Fermat theorem
        # which "states" that 1 (neutral element) is always the last element to be generated
        total += 1

        self._total = total
        self._p = self._get_prime(total)
        self._g = 0

        factors = self.pFactors(self._p - 1)
        while True:
            self._g = int(os.urandom(16).encode('hex'), 16) % self._p

            # This test is required to ensure that g is large enough to "always" wrap
            # around the modulus p; this helps "randomizing" the accumulator a
            if self._g <= math.sqrt(self._p):
                continue
            ok = True
            for factor in factors:
                if 1 == pow(gmpy2.mpz(self._g), gmpy2.mpz((self._p-1)/factor)) % gmpy2.mpz(self._p):
                    ok = False
                    break
            if ok:
                break

        self._acc = self._g

    def _get_prime(self, total):
        n = total

        if n % 2 == 0:
            n += 1

        while not self.isPrime(n):
            n += 2

        return n

    ##########################################################################
    # Primality Testing with the Rabin-Miller Algorithm
    # http://inventwithpython.com/hacking (BSD Licensed)
    def rabinMiller(self, num):
        # Returns True if num is a prime number.

        s = num - 1
        t = 0
        while s % 2 == 0:
            # keep halving s while it is even (and use t
            # to count how many times we halve s)
            s = s // 2
            t += 1

        for trials in range(5):  # try to falsify num's primality 5 times
            a = random.randrange(2, num - 1)
            v = pow(a, s, num)
            if v != 1:  # this test does not apply if v is 1.
                i = 0
                while v != (num - 1):
                    if i == t - 1:
                        return False
                    else:
                        i = i + 1
                        v = (v ** 2) % num
        return True

    def isPrime(self, num):
        # Return True if num is a prime number. This function does a quicker
        # prime number check before calling rabinMiller().

        if (num < 2):
            return False  # 0, 1, and negative numbers are not prime

        # About 1/3 of the time we can quickly determine if num is not prime
        # by dividing by the first few dozen prime numbers. This is quicker
        # than rabinMiller(), but unlike rabinMiller() is not guaranteed to
        # prove that a number is prime.
        lowPrimes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97,
                     101, 103, 107, 109, 113, 127, 131, 137, 139, 149, 151, 157, 163, 167, 173, 179, 181, 191, 193, 197,
                     199, 211, 223, 227, 229, 233, 239, 241, 251, 257, 263, 269, 271, 277, 281, 283, 293, 307, 311, 313,
                     317, 331, 337, 347, 349, 353, 359, 367, 373, 379, 383, 389, 397, 401, 409, 419, 421, 431, 433, 439,
                     443, 449, 457, 461, 463, 467, 479, 487, 491, 499, 503, 509, 521, 523, 541, 547, 557, 563, 569, 571,
                     577, 587, 593, 599, 601, 607, 613, 617, 619, 631, 641, 643, 647, 653, 659, 661, 673, 677, 683, 691,
                     701, 709, 719, 727, 733, 739, 743, 751, 757, 761, 769, 773, 787, 797, 809, 811, 821, 823, 827, 829,
                     839, 853, 857, 859, 863, 877, 881, 883, 887, 907, 911, 919, 929, 937, 941, 947, 953, 967, 971, 977,
                     983, 991, 997]

        if num in lowPrimes:
            return True

        # See if any of the low prime numbers can divide num
        for prime in lowPrimes:
            if (num % prime == 0):
                return False

        # If all else fails, call rabinMiller() to determine if num is a prime.
        return self.rabinMiller(num)
    ##########################################################################

    # Return prime factors of n
    @staticmethod
    def pFactors(n):
        """Finds the prime factors of 'n'"""
        from math import sqrt
        pFact, limit, check, num = [], int(sqrt(n)) + 1, 2, n
        if n == 1: return [1]
        for check in range(2, limit):
            while num % check == 0:
                pFact.append(check)
                num /= check
        if num > 1:
            pFact.append(num)
        return set(pFact)



    # Provides a "random" number between 0 and p - 1
    # If a number is about to be returned a second time, an Exception is raised
    def get_random(self):
        while self._acc != 1:
            if self._acc < self._total:
                yield self._acc - 1
            self._acc = (self._acc * self._g) % self._p
        raise StopIteration()
