# Dice parser using Pratt parsing
# see https://matklad.github.io/2020/04/13/simple-but-powerful-pratt-parsing.html


ND_CAP = 100 # 超过这个值的单次掷骰采用快速算法，或者直接拒绝计算了



import re, dataclasses, math, random, string,typing
from algorithms import mdn, mdnsr, mdnlr, binomial


binary_ops = {
    '+': ((1, 2), lambda x, y: x + y), # (left binding precedence, right binding precedence), function 
    '-': ((1, 2), lambda x, y: x - y), # left < right: evaluate from left to right, vice versa
    '*': ((3, 4), lambda x, y: x * y),
    '/': ((3, 4), lambda x, y: x / y),
    '%': ((3, 4), lambda x, y: x % y),
    '//': ((3, 4), lambda x, y: x // y),
    '**': ((7, 6), lambda x, y: x ** y),
    }

unary_ops = {
    '+': (5, lambda x: x), # right binding precedence, function
    '-': (5, lambda x: -x),
    }

unary_ops_symbolic = {
    'exp': (10, math.exp),
    'log': (10, math.log),
    'log10': (10, math.log10),
    'sin': (10, math.sin),
    'cos': (10, math.cos),
    'abs': (10, abs),
    'sqrt': (10, math.sqrt),
    'ceil': (10, math.ceil),
    'floor': (10, math.floor),
    'round': (10, round),
    }

unary_ops.update(unary_ops_symbolic)

suffixes = {
    '!': (11, math.factorial),
    }

fns = {
    'max': max,
    'min': min,
    }

constants = {
    'pi': lambda: ConstantExpr(math.pi),
    'Pi': lambda: ConstantExpr(math.pi),
    }

ops = tuple(sorted(set(binary_ops).union(unary_ops, suffixes, fns, constants), key=len, reverse=True))
symbolics = set(unary_ops_symbolic).union(fns, constants, {'('})

identifier_chars = string.digits + string.ascii_letters + '_'

class IllegalExpr(ValueError):
    
    def __init__(self, msg: str):
        ValueError.__init__(self, msg)
    
    
class DiceOverflow(ValueError):

    def __init__(self, msg: str):
        ValueError.__init__(self, msg)


@dataclasses.dataclass
class DiceExpr:
    nd: int     # 骰子个数
    nf: int     # 骰子面数
    sl: str     # 骰子取最大还是最小的几个 'l'是取最大nsl个，'s'是取最小nsl个
    nsl: int
    
    def __str__(self):
        nd_str = str(self.nd) if self.nd != 1 else ''
        if self.nsl < self.nd:
            return f'{nd_str}d{self.nf}{self.sl}{self.nsl if self.nsl != 1 else ""}'
        return f'{nd_str}d{self.nf}'

    def roll(self):
        if self.nd <= ND_CAP:
            dices = [random.randrange(self.nf) + 1 for _ in range(self.nd)]
            val = sum(sorted(dices, reverse=(self.sl == 'l'))[: self.nsl])
            return val, (self, dices, val)
        
        if self.nsl == self.nd:
            val = mdn(self.nd, self.nf)
            return val, (self, None, val)
        if self.sl == 'l':
            val = mdnlr(self.nd, self.nf, self.nsl)
        else:
            val = mdnsr(self.nd, self.nf, self.nsl)
        return val, (self, None, val)
    
    def evaluate(self):
        val, dices = self.roll()
        yield dices
        return val
    

@dataclasses.dataclass
class CoCBPRollExpr: # dp = max(d10, d10) * 10 + d10 - 10
    nd: int            # db = min(d10, d10) * d10 + d10 - 10
    bp: str            # 3db = db + db + db
    
    def __str__(self):
        nd_str = str(self.nd) if self.nd != 1 else ''
        return f'{nd_str}d{self.bp}'
    
    def roll(self):
        if self.nd > ND_CAP:
            tens = 0
            nd = self.nd
            for i in reversed(range(10)):
                ni = binomial(nd, (2 * i + 1) / (i + 1) ** 2)
                nd -= ni
                tens += i * ni
            val = tens * 10 + mdn(self.nd, 10)
            return val, (self, None, val)
            # raise DiceOverflow(f'Too many dices: {self}')
        dices = []
        val = 0
        for _ in range(self.nd):
            dices1 = (random.randrange(10), random.randrange(10))
            dice2 = random.randrange(10) + 1
            val += max(dices1) * 10 + dice2 if self.bp == 'p' else min(dices1) * 10 + dice2
            dices.append(tuple(d * 10 + dice2 for d in dices1))
        return val, (self, dices, val)
    
    def evaluate(self):
        val, dices = self.roll()
        yield dices
        return val
    

class Lexer:
    
    def __init__(self, input: str):
        
        self.tokens = []
        
        input = input.strip(' \n')
        while input:
            if input[0] in ' \n':
                input = input[1:]
                continue
            
            if input[0] in '(),':
                self.tokens.append(input[0])
                input = input[1:]
                continue
            
            match_flag = False
            for o in ops:
                if input.startswith(o):
                    if o in symbolics and len(input) > len(o) and input[len(o)] in identifier_chars:
                        continue
                    self.tokens.append(o)
                    input = input[len(o):]
                    match_flag = True
                    break
            if match_flag:
                continue
            
            # match 3d100s1 expressions
            m = re.match(
                r'(?P<nd>[0-9]*)[dD](?P<nf>[0-9]+)((?P<sl>[slSL])(?P<nsl>[0-9]*))?',
                input)
            if m:
                input = input[len(m[0]):]
                nd = int(m['nd']) if m['nd'] else 1
                nf = int(m['nf'])
                if m['sl'] is not None:
                    sl, nsl = m['sl'].lower(), int(m['nsl']) if m['nsl'] else 1
                else:
                    sl, nsl = 's', nd
                if nsl > nd or nf <= 0 or nd < 0 or nsl < 0:
                    raise IllegalExpr(f'Bad dice: {m[0]}')
                self.tokens.append(DiceExpr(nd=nd, nf=nf, sl=sl, nsl=nsl))
                continue
            
            # match db or 3dp for CoC bonus/penalized roll
            m = re.match(r'(?P<nd>[0-9]*)[dD](?P<bp>[bpBP])', input)
            if m:
                input = input[len(m[0]):]
                nd = int(m['nd']) if m['nd'] else 1
                self.tokens.append(CoCBPRollExpr(nd, m['bp'].lower()))
                continue
            
            # match a int or float
            m = re.match(
                r'((?P<int>[0-9]+)(?P<frac>\.[0-9]*)?|(?P<frac1>.[0-9]+))(?P<exp>[eE]-?[0-9]+)?', 
                input)
            if m:
                input = input[len(m[0]):]
                if m['frac'] or m['frac1'] or m['exp']:
                    self.tokens.append(float(m[0]))
                else:
                    self.tokens.append(int(m['int']))
                continue
            
            raise IllegalExpr(f'Illegal Expression "{input}"')


class CompositeExpr:
    
    def __init__(self, op, args: list, name=''):
        self.op = op
        self.args = args
        self.name = name if name else '_not_named'
    
    def __repr__(self):
        return f'CompositeExpr({self.op}, {self.args}, {repr(self.name)})'
    
    def __str__(self):
        return f'{self.name}({", ".join(str(a) for a in self.args)})'
    
    def evaluate(self):
        a = []
        for arg in self.args:
            a.append((yield from arg.evaluate()))
        return self.op(*a)
        
        # disallowed since python 3.8
        # return self.op(*[(yield from arg.evaluate()) for arg in self.args])


@dataclasses.dataclass
class ConstantExpr:
    
    value: typing.Union[int, float]
    # def __init__(self, value):
    #     self.value = value
    
    def __repr__(self):
        return f'ConstantExpr({self.value})'
    
    def __str__(self):
        return str(self.value)
    
    def evaluate(self):
        return self.value
        yield
    

def parse(tokens: list, min_bp=-1):
    
    tok = tokens.pop(0)
    may_follow_symbolic = True
    if isinstance(tok, (int, float)):
        lhs = ConstantExpr(tok)
    elif isinstance(tok, (DiceExpr, CoCBPRollExpr)):
        lhs = tok
        may_follow_symbolic = False
    elif tok in unary_ops:
        precedence, op_fn = unary_ops[tok]
        lhs = CompositeExpr(op_fn, [parse(tokens, precedence)], name=tok)
    elif tok in fns:
        op_fn = fns[tok]
        if len(tokens) == 0 or tokens.pop(0) != '(':
            raise IllegalExpr(f'Parsing error: function {tok} not followed by "(" at {tokens}')
        args, delim = [], ','
        while delim != ')':
            args.append(parse(tokens, 0))
            if len(tokens) == 0:
                raise IllegalExpr(f'Parsing error: unbalanced brackets at {tokens}')
            delim = tokens.pop(0)
            if delim not in ',)':
                raise IllegalExpr(f'Parsing error: unrecognized symbol at {tokens}')
        lhs = CompositeExpr(op_fn, args, name=tok)
    elif tok in constants:
        lhs = constants[tok]()
    elif tok == '(':
        lhs = parse(tokens, 0)
        if len(tokens) == 0 or tokens.pop(0) != ')':
            raise IllegalExpr(f'Parsing error: unbalanced brackets at {tokens}')
    else:
        raise IllegalExpr(f'Parsing error: {tokens}')
    
    while tokens:
        
        op = tokens[0]
        
        if op in suffixes:
            if suffixes[op][0] < min_bp:
                break
            tokens.pop(0)
            lhs = CompositeExpr(suffixes[op][1], [lhs], op)
            continue
        
        if op not in binary_ops:
            if may_follow_symbolic and op in symbolics:
                (l_bp, r_bp), op_fn = binary_ops['*']
                if l_bp < min_bp:
                    break
                lhs = CompositeExpr(op_fn, [lhs, parse(tokens, r_bp)], '*')
                continue
            else:
                break
        
        (l_bp, r_bp), op_fn = binary_ops[op]
        if l_bp < min_bp:
            break
        tokens.pop(0)
        
        lhs = CompositeExpr(op_fn, [lhs, parse(tokens, r_bp)], op)
    
    if min_bp < 0 and tokens:
        raise IllegalExpr(f'Parsing Error: unhandled trailing ops: {tokens}')
    
    return lhs


def eval_expr(expr):
    def _inner(ret: list, expr):
        ret.append((yield from expr.evaluate()))
    ret = []
    summary = list(_inner(ret, expr))
    return ret[0], summary


def parse_and_eval_dice(expr: str):
    
    def summarizer(dice_expr, dices, val):
        if isinstance(dice_expr, DiceExpr):
            if dices is None:
                return f'{dice_expr} = {val}' 
            dice_sort = sorted(((v, i) for i, v in enumerate(dices)), reverse=(dice_expr.sl == 'l'))
            dice_sort = sorted((i, v, rank < dice_expr.nsl and dice_expr.nsl < dice_expr.nd) for rank, (v, i) in enumerate(dice_sort))
            return f'{dice_expr} = {val}: ' + ', '.join(f'[{v}]' if z else str(v) for i, v, z in dice_sort)
        elif isinstance(dice_expr, CoCBPRollExpr):
            if dices is None:
                return f'{dice_expr} = {val}'
            return f'{dice_expr} = {val}: ' + ", ".join(f'{{{d[0]},{d[1]}}}' for d in dices)
    
    try:
        e = parse(Lexer(expr).tokens)
    except DiceOverflow:
        yield '没这么多骰子'
        return
    except IllegalExpr or TypeError or ValueError:
        yield '表达式有问题'
        return
    
    ret, summary = eval_expr(e)
    for s in summary:
        yield summarizer(*s)
    if len(summary) != 1 or isinstance(e, CompositeExpr):
        yield f'结果：{ret}'
    

if __name__ == '__main__':
    print(__doc__)
    
    def summarizer(dice_expr, dices, val):
        if isinstance(dice_expr, DiceExpr):
            if dices is None:
                return f'{dice_expr} = {val}' 
            dice_sort = sorted(((v, i) for i, v in enumerate(dices)), reverse=(dice_expr.sl == 'l'))
            dice_sort = sorted((i, v, rank < dice_expr.nsl and dice_expr.nsl < dice_expr.nd) for rank, (v, i) in enumerate(dice_sort))
            return f'{dice_expr} = {val}: ' + ', '.join(f'[{v}]' if z else str(v) for i, v, z in dice_sort)
        elif isinstance(dice_expr, CoCBPRollExpr):
            if dices is None:
                return f'{dice_expr} = {val}'
            return f'{dice_expr} = {val}: ' + ", ".join(f'{{{d[0]},{d[1]}}}' for d in dices)

    try:
        expr = '3pi+4log10(1000000000000d9999999999999999s5555555555)sin 5! +1000000dp+ abs(5d9l3 +-2e-4* max(2Dp, 100., 5d40))*8**(3*-7d8%2+4.)'
        print(expr)
        e = parse(Lexer(expr).tokens)
        print(e)
        
        ret, summary = eval_expr(e)
        for s in summary:
            print(summarizer(*s))
        if len(summary) != 1 or isinstance(e, CompositeExpr):
            print(f'Result: {ret}')
    
    except DiceOverflow:
        print('没这么多骰子')
    except IllegalExpr or TypeError or ValueError:
        print('表达式有问题')
    
    print('\n'.join(parse_and_eval_dice(expr)))
                
                    