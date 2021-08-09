import math, random


def binomial(n: int, p: float) -> int:
    # if p < 0 or p > 1:
    #     raise ValueError(f'invalid p = {p}')
    
    if n == 0:
        return 0
    
    if n % 2 == 0:
        return int(random.random() < p) + binomial(n - 1, p)
    
    median = random.betavariate(n // 2 + 1, n // 2 + 1)
    
    if median < p:
        return n // 2 + 1 + binomial(n // 2, (p - median) / (1 - median))
    else:
        return binomial(n // 2, p / median)


def mdn(m: int, n: int) -> int: # m个n面骰
    return _mdn(m, n) + m

def _mdn(m: int, n: int) -> int: # m个n面骰，但是每个骰子是0到n-1
    m_cap = 10
    
    if n == 1:
        return 0
    
    if m < m_cap:
        return sum(random.randrange(n) for _ in range(m))
    
    n_p2round_log = (n - 1).bit_length() - 1
    nround = 1 << n_p2round_log
    m_lower = binomial(m, n / nround)
    m_upper = m - m_lower
    
    return m_upper * nround + _mdn(m_upper, n - nround) + _md2pn(m_lower, n_p2round_log)

def _md2pn(m: int, n: int) -> int: # m个2**n面骰，每个骰子是0到2**n-1
    return sum(2 ** i * binomial(m, 0.5) for i in range(n))

def mdnsr(m: int, n: int, r: int):
    if r == 0:
        return 0
    quantile = random.betavariate(r, m - r + 1)
    ipart = math.floor(n * quantile)
    fpart = n * quantile - ipart
    m_frac = binomial(m, fpart / (n * quantile))
    return m_frac * ipart + _mdn(m - m_frac, ipart) + r

def mdnlr(m: int, n: int, r: int):
    return (n + 1) * r - mdnsr(m, n, r)


if __name__ == '__main__':
    print(mdnlr(
        100000000000000000000, 
        9999999999999999999999999999999999999999,
        5555555555555555555))