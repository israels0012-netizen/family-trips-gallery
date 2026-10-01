# -*- coding: utf-8 -*-
"""Minimal Power Fx interpreter for verifying the V97 Canvas app formulas.

Not Microsoft's implementation. Models the subset of Power Fx used by the app,
including record scopes / As aliases, behavior chaining, IfError, ParseJSON
untyped values, collections, and a SharePoint list mock with delegation limits.
"""
import json, math, re, uuid, datetime

# ============================================================== lexer
class Tok:
    __slots__ = ('k', 'v', 'p')
    def __init__(s, k, v, p): s.k, s.v, s.p = k, v, p
    def __repr__(s): return f'{s.k}:{s.v!r}'

OPS = ['<=', '>=', '<>', '&&', '||', '=', '<', '>', '&', '+', '-', '*', '/', '^', '!', '(', ')', '{', '}', '[', ']', ',', ';', ':', '.', '%', '@']

def lex(src):
    toks = []; i = 0; n = len(src)
    while i < n:
        c = src[i]
        if c in ' \t\r\n ':
            i += 1; continue
        if c == '/' and src.startswith('//', i):
            j = src.find('\n', i); i = n if j < 0 else j; continue
        if c == '"':
            j = i + 1; buf = []
            while True:
                if j >= n: raise SyntaxError('unterminated string at %d' % i)
                if src[j] == '"':
                    if j + 1 < n and src[j + 1] == '"':
                        buf.append('"'); j += 2; continue
                    break
                buf.append(src[j]); j += 1
            toks.append(Tok('str', ''.join(buf), i)); i = j + 1; continue
        if c == "'":
            j = src.index("'", i + 1)
            toks.append(Tok('id', src[i + 1:j], i)); i = j + 1; continue
        if c.isdigit() or (c == '.' and i + 1 < n and src[i + 1].isdigit()):
            m = re.match(r'\d*\.?\d+(?:[eE][+-]?\d+)?', src[i:])
            toks.append(Tok('num', float(m.group(0)), i)); i += len(m.group(0)); continue
        if c.isalpha() or c == '_':
            m = re.match(r'[A-Za-z_][A-Za-z0-9_]*', src[i:])
            toks.append(Tok('id', m.group(0), i)); i += len(m.group(0)); continue
        for op in OPS:
            if src.startswith(op, i):
                toks.append(Tok('op', op, i)); i += len(op); break
        else:
            raise SyntaxError('bad char %r at %d' % (c, i))
    toks.append(Tok('eof', None, n))
    return toks

# ============================================================== parser
# AST nodes are tuples: (kind, ...)
class Parser:
    def __init__(s, src):
        s.src = src; s.t = lex(src); s.i = 0
    def peek(s, k=0): return s.t[s.i + k]
    def nxt(s):
        t = s.t[s.i]; s.i += 1; return t
    def accept(s, k, v=None):
        t = s.peek()
        if t.k == k and (v is None or t.v == v):
            s.i += 1; return t
        return None
    def expect(s, k, v=None):
        t = s.accept(k, v)
        if not t:
            raise SyntaxError('expected %s %s at %d got %r' % (k, v, s.peek().p, s.peek()))
        return t
    def parse(s):
        e = s.chain()
        if s.peek().k != 'eof':
            raise SyntaxError('trailing tokens at %d: %r' % (s.peek().p, s.peek()))
        return e
    def chain(s):
        items = [s.expr()]
        while s.accept('op', ';'):
            if s.peek().k == 'eof' or (s.peek().k == 'op' and s.peek().v in (')', ',')):
                break
            items.append(s.expr())
        return items[0] if len(items) == 1 else ('chain', items)
    def expr(s): return s.orx()
    def orx(s):
        l = s.andx()
        while True:
            if s.accept('op', '||') or s.accept('id', 'Or'):
                l = ('or', l, s.andx())
            else: return l
    def andx(s):
        l = s.cmp()
        while True:
            if s.accept('op', '&&') or s.accept('id', 'And'):
                l = ('and', l, s.cmp())
            else: return l
    def cmp(s):
        l = s.cat()
        while True:
            t = s.peek()
            if t.k == 'op' and t.v in ('=', '<>', '<', '>', '<=', '>='):
                s.nxt(); l = ('bin', t.v, l, s.cat())
            elif t.k == 'id' and t.v in ('in', 'exactin'):
                s.nxt(); l = ('bin', t.v, l, s.cat())
            else: return l
    def cat(s):
        l = s.add()
        while s.accept('op', '&'):
            l = ('bin', '&', l, s.add())
        return l
    def add(s):
        l = s.mul()
        while True:
            t = s.peek()
            if t.k == 'op' and t.v in ('+', '-'):
                s.nxt(); l = ('bin', t.v, l, s.mul())
            else: return l
    def mul(s):
        l = s.pow()
        while True:
            t = s.peek()
            if t.k == 'op' and t.v in ('*', '/'):
                s.nxt(); l = ('bin', t.v, l, s.pow())
            else: return l
    def pow(s):
        l = s.unary()
        if s.accept('op', '^'):
            return ('bin', '^', l, s.pow())
        return l
    def unary(s):
        if s.accept('op', '!') or s.accept('id', 'Not'):
            return ('not', s.unary())
        if s.accept('op', '-'):
            return ('neg', s.unary())
        if s.accept('op', '+'):
            return s.unary()
        return s.postfix()
    def postfix(s):
        e = s.primary()
        while True:
            if s.accept('op', '.'):
                t = s.nxt()
                if t.k != 'id': raise SyntaxError('member name expected at %d' % t.p)
                e = ('dot', e, t.v)
            elif s.accept('op', '%'):
                e = ('bin', '/', e, ('num', 100.0))
            else:
                return e
    def primary(s):
        t = s.nxt()
        if t.k == 'num': return ('num', t.v)
        if t.k == 'str': return ('str', t.v)
        if t.k == 'op' and t.v == '(':
            e = s.chain(); s.expect('op', ')'); return e
        if t.k == 'op' and t.v == '{':
            fields = []
            if not s.accept('op', '}'):
                while True:
                    k = s.nxt()
                    if k.k not in ('id', 'str'): raise SyntaxError('field name at %d' % k.p)
                    s.expect('op', ':')
                    fields.append((k.v, s.expr()))
                    if s.accept('op', '}'): break
                    s.expect('op', ',')
            return ('rec', fields)
        if t.k == 'op' and t.v == '[':
            items = []
            if not s.accept('op', ']'):
                while True:
                    items.append(s.expr())
                    if s.accept('op', ']'): break
                    s.expect('op', ',')
            return ('arr', items)
        if t.k == 'id':
            if t.v in ('true', 'false'): return ('bool', t.v == 'true')
            if s.peek().k == 'op' and s.peek().v == '(':
                s.nxt(); args = []
                if not s.accept('op', ')'):
                    while True:
                        a = s.chain()
                        if s.accept('id', 'As'):
                            a = ('as', a, s.expect('id').v)
                        args.append(a)
                        if s.accept('op', ')'): break
                        s.expect('op', ',')
                return ('call', t.v, args, t.p)
            return ('id', t.v, t.p)
        raise SyntaxError('unexpected %r at %d' % (t, t.p))

_PCACHE = {}
def parse(src):
    if src.startswith('='): src = src[1:]
    p = _PCACHE.get(src)
    if p is None:
        p = Parser(src).parse(); _PCACHE[src] = p
    return p

# ============================================================== values
class PfxError(Exception):
    def __init__(s, msg, kind='Custom'):
        super().__init__(msg); s.msg = msg; s.kind = kind

class Untyped:
    __slots__ = ('v',)
    def __init__(s, v): s.v = v
    def __repr__(s): return 'U(%r)' % (s.v,)

class Table(list):
    pass

class Enum:
    def __init__(s, name): s.name = name
    def __repr__(s): return s.name
    def __eq__(s, o): return isinstance(o, Enum) and o.name == s.name
    def __hash__(s): return hash(s.name)

class Color(tuple): pass

def isblank(v):
    return v is None or v == '' or (isinstance(v, Untyped) and v.v is None)

def tonum(v):
    if v is None: return 0.0
    if isinstance(v, bool): return 1.0 if v else 0.0
    if isinstance(v, (int, float)): return float(v)
    if isinstance(v, str):
        if v.strip() == '': return 0.0
        try: return float(v.replace(',', ''))
        except ValueError: raise PfxError('Value is not a number: %r' % v, 'InvalidArgument')
    if isinstance(v, Untyped):
        if v.v is None: return None
        if isinstance(v.v, bool): raise PfxError('untyped bool to number')
        if isinstance(v.v, (int, float)): return float(v.v)
        if isinstance(v.v, str): return tonum(v.v)
        raise PfxError('untyped to number: %r' % (v.v,))
    if isinstance(v, datetime.datetime): return v.timestamp()
    raise PfxError('cannot convert %r to number' % (v,))

def fmt_general(x):
    if x is None: return ''
    if isinstance(x, bool): return 'true' if x else 'false'
    if isinstance(x, float):
        if x == int(x) and abs(x) < 1e15: return str(int(x))
        r = repr(x)
        if 'e' in r:
            return ('%.15f' % x).rstrip('0').rstrip('.')
        # Power Fx keeps ~15 significant digits
        s = '%.15g' % x
        return s
    if isinstance(x, int): return str(x)
    return str(x)

def totext(v):
    if v is None: return ''
    if isinstance(v, str): return v
    if isinstance(v, bool): return 'true' if v else 'false'
    if isinstance(v, (int, float)): return fmt_general(float(v))
    if isinstance(v, Untyped):
        if v.v is None: return None
        if isinstance(v.v, str): return v.v
        if isinstance(v.v, bool): return 'true' if v.v else 'false'
        if isinstance(v.v, (int, float)): return fmt_general(float(v.v))
        raise PfxError('untyped object/array to text')
    if isinstance(v, datetime.datetime): return v.strftime('%d/%m/%Y %H:%M')
    if isinstance(v, Enum): return v.name.split('.')[-1]
    raise PfxError('cannot convert %r to text' % (type(v),))

def tobool(v):
    if v is None: return False
    if isinstance(v, bool): return v
    if isinstance(v, (int, float)): return v != 0
    if isinstance(v, Untyped):
        if isinstance(v.v, bool): return v.v
        if v.v is None: return False
        raise PfxError('untyped to boolean')
    if isinstance(v, str):
        if v.lower() == 'true': return True
        if v.lower() == 'false' or v == '': return False
    raise PfxError('cannot convert %r to boolean' % (v,))

def format_number(x, fmt, locale='en-US'):
    if x is None: return ''
    x = float(x)
    if fmt in ('hh:mm',): raise PfxError('date format on number')
    m = re.fullmatch(r'(#,##)?(0*)(?:\.([0#]+))?', fmt.replace('#,##0', '#,##0'))
    m = re.fullmatch(r'(#,##0|0)(?:\.(0*)(#*))?', fmt)
    if not m: raise PfxError('unsupported number format ' + fmt)
    grouping = m.group(1) == '#,##0'
    req = len(m.group(2) or ''); opt = len(m.group(3) or '')
    nd = req + opt
    q = round(abs(x) + 0.0, nd)
    s = ('%.' + str(nd) + 'f') % q if nd else '%d' % round(abs(x))
    if '.' in s:
        ip, fp = s.split('.')
        if opt:
            fp = fp[:req] + fp[req:].rstrip('0')
    else:
        ip, fp = s, ''
    if grouping:
        ip = '{:,}'.format(int(ip))
    out = ip + ('.' + fp if fp else '')
    neg = x < 0 and float(s.replace(',', '')) != 0
    return ('-' if neg else '') + out

# ============================================================== SharePoint mock
SP_COLUMNS = ['Title', 'AuditNote', 'AuditStatus', 'EvidenceUrl'] + ['field_%d' % i for i in range(1, 22) if i != 13]
DELEGABLE_NUM = {'field_10', 'field_11', 'field_13'}
DELEGABLE_TEXT = {'field_1', 'field_2', 'field_3', 'field_14', 'field_17', 'Title'}

class SPList:
    def __init__(s, limit=500):
        s.rows = []; s.next_id = 1; s.limit = limit; s.fail_next = 0; s.fail_pred = None
        s.clock = datetime.datetime(2026, 9, 29, 20, 0, 0)
        s.queries = 0
    def tick(s, minutes=0, seconds=1):
        s.clock += datetime.timedelta(minutes=minutes, seconds=seconds)
    def insert(s, rec):
        if s.fail_next > 0 or (s.fail_pred and s.fail_pred(rec)):
            if s.fail_next > 0: s.fail_next -= 1
            raise PfxError('simulated network failure', 'Network')
        r = {c: None for c in SP_COLUMNS}
        r.update({'ID': s.next_id, 'Created': s.clock})
        s.next_id += 1
        for k, v in rec.items():
            if k in ('ID', 'Created'): continue
            if k not in SP_COLUMNS: raise PfxError('SharePoint column does not exist: ' + k, 'Name')
            r[k] = v
        s.rows.append(r); s.tick()
        return dict(r)
    def update(s, rid, changes):
        for r in s.rows:
            if r['ID'] == rid:
                r.update({k: v for k, v in changes.items() if k not in ('ID', 'Created')})
                return dict(r)
        raise PfxError('record not found')

class DSQuery:
    """lazy delegable query over SPList"""
    def __init__(s, sp, pred=None, pred_env=None, sorts=None, delegable=True):
        s.sp, s.pred, s.pred_env, s.sorts, s.delegable = sp, pred, pred_env, sorts or [], delegable
    def materialize(s, interp):
        sp = s.sp; sp.queries += 1
        if s.delegable:
            rows = [dict(r) for r in sp.rows if s.pred is None or interp.eval_pred_row(s.pred, s.pred_env, r)]
            if s.sorts: rows = sort_rows(rows, s.sorts)
            return Table(rows[:sp.limit])
        base = [dict(r) for r in sp.rows[:sp.limit]]
        rows = [r for r in base if s.pred is None or interp.eval_pred_row(s.pred, s.pred_env, r)]
        if s.sorts: rows = sort_rows(rows, s.sorts)
        interp.warn('non-delegable query materialized')
        return Table(rows)

def sort_key_val(v):
    if v is None: return (0, 0)
    if isinstance(v, (int, float)): return (1, v)
    if isinstance(v, datetime.datetime): return (1, v.timestamp())
    if isinstance(v, bool): return (1, int(v))
    return (2, str(v))

def sort_rows(rows, sorts):
    rows = list(rows)
    for col, desc in reversed(sorts):
        rows.sort(key=lambda r: sort_key_val(r.get(col) if not callable(col) else col(r)), reverse=desc)
    return rows

# ============================================================== interpreter
class Scope:
    __slots__ = ('rec', 'alias', 'names')
    def __init__(s, rec=None, alias=None, names=None):
        s.rec, s.alias, s.names = rec, alias, names

class Ctrl:
    def __init__(s, name, ctype, props, parent):
        s.name, s.ctype, s.props, s.parent = name, ctype, props, parent
        s.state = {}

ENUMS = {}
for e in ['SortOrder.Ascending', 'SortOrder.Descending', 'NotificationType.Error', 'NotificationType.Warning', 'NotificationType.Success',
          'NotificationType.Information', 'JSONFormat.Compact', 'DateTimeFormat.UTC', 'TimeUnit.Minutes', 'TimeUnit.Seconds', 'TimeUnit.Days',
          'MatchOptions.Contains', 'ErrorKind.Custom', 'DisplayMode.Edit', 'DisplayMode.Disabled', 'DisplayMode.View', 'TextMode.MultiLine',
          'Align.Right', 'Align.Center', 'Align.Left', 'VerticalAlign.Middle', 'VerticalAlign.Top', 'Font.Arial', 'FontWeight.Normal',
          'FontWeight.Semibold', 'FontWeight.Bold', 'ImagePosition.Stretch', 'ImagePosition.Fit', 'ScreenTransition.None']:
    ENUMS[e] = Enum(e)

class App:
    def __init__(s, doc_nodes, sp=None, width=1440, height=900, user='User A'):
        s.ctrls = {}
        s.order = []
        s.globals = {}
        s.cols = {}
        s.sp = sp or SPList()
        s.width, s.height = width, height
        s.user = user
        s.queue = []
        s.notes = []
        s.warnings = []
        s.clipboard = None
        s.launched = []
        s.guid_n = 0
        s._add(doc_nodes, None)
        s.trace = False
    def _add(s, nodes, parent):
        for n in nodes:
            (name, body), = n.items()
            c = Ctrl(name, body.get('Control'), body.get('Properties', {}), parent)
            s.ctrls[name] = c; s.order.append(name)
            if body.get('Children'): s._add(body['Children'], name)
    def warn(s, m): s.warnings.append(m)
    def now(s): return s.sp.clock

    # ---------------- control property evaluation
    def prop(s, cname, pname, scope=None, item=None):
        c = s.ctrls[cname]
        if pname in ('Text',) and c.ctype and 'TextInput' in c.ctype:
            if 'text' not in c.state:
                c.state['text'] = totext(s.prop(cname, 'Default')) if 'Default' in c.props else ''
            return c.state['text']
        if pname == 'AllItems' and c.ctype and c.ctype.startswith('Gallery'):
            return s.prop(cname, 'Items')
        if pname == 'Default' and 'Default' not in c.props: return ''
        if pname not in c.props:
            if pname in ('X', 'Y'): return 0.0
            if pname == 'Visible': return True
            if pname == 'TemplateWidth':
                return s.prop(cname, 'Width') / tonum(s.prop(cname, 'WrapCount') if 'WrapCount' in c.props else 1)
            if pname == 'Height' and c.ctype and c.ctype.startswith('Gallery'): return 0.0
            raise PfxError('no property %s.%s' % (cname, pname), 'Name')
        f = c.props[pname]
        if not isinstance(f, str) or not f.startswith('='):
            return f
        env = {'ctrl': cname}
        if item is not None: env['thisitem'] = item
        return s.eval(parse(f), [] if scope is None else scope, env)

    def set_text(s, cname, text):
        s.ctrls[cname].state['text'] = text

    def select(s, cname, item=None):
        """user click: run OnSelect then drain queue"""
        s.run(cname, item)
        s.drain()

    def run(s, cname, item=None):
        c = s.ctrls[cname]
        f = c.props.get('OnSelect') or c.props.get('OnChange')
        if not f: return
        scope = [Scope(rec=item)] if item is not None else []
        env = {'ctrl': cname, 'thisitem': item}
        try:
            s.eval(parse(f), scope, env)
        except PfxError as e:
            s.notes.append(('UNHANDLED', '%s: %s' % (cname, e.msg)))

    def change(s, cname):
        c = s.ctrls[cname]
        f = c.props.get('OnChange')
        if f:
            try: s.eval(parse(f), [], {'ctrl': cname})
            except PfxError as e: s.notes.append(('UNHANDLED', '%s: %s' % (cname, e.msg)))
            s.drain()

    def drain(s, limit=200):
        n = 0
        while s.queue:
            nm = s.queue.pop(0)
            s.run(nm)
            n += 1
            if n > limit: raise RuntimeError('select loop')

    # ---------------- name resolution
    def lookup(s, name, scope, env, node):
        for sc in reversed(scope):
            if sc.names and name in sc.names: return sc.names[name]
            if sc.alias == name: return sc.rec
            if sc.alias is None and isinstance(sc.rec, dict) and name in sc.rec: return sc.rec[name]
        if name == 'ThisRecord':
            for sc in reversed(scope):
                if sc.alias is None and sc.rec is not None: return sc.rec
            raise PfxError('ThisRecord outside scope')
        if name == 'ThisItem':
            ti = env.get('thisitem')
            if ti is None: raise PfxError('ThisItem outside gallery', 'Name')
            return ti
        if name in s.cols: return s.cols[name]
        if name in s.globals: return s.globals[name]
        if name.startswith('var'): return None   # uninitialized global
        if name.startswith('col'): return Table()
        if name in s.ctrls: return ('ctrl', name)
        if name == 'Parent': return ('parent', env.get('ctrl'))
        if name == 'Self': return ('ctrl', env.get('ctrl'))
        if name == 'DashboardPOC_Data': return ('ds',)
        raise PfxError('UNBOUND %s' % name, 'Name')

    def eval_pred_row(s, pred, penv, row):
        scope, env, alias = penv
        return tobool(s.eval(pred, scope + [Scope(rec=row, alias=alias)], env))

    # ---------------- evaluation
    def eval(s, n, scope, env):
        k = n[0]
        if k == 'num': return n[1]
        if k == 'str': return n[1]
        if k == 'bool': return n[1]
        if k == 'id': return s.lookup(n[1], scope, env, n)
        if k == 'chain':
            r = None
            for it in n[1]:
                r = s.eval(it, scope, env)
            return r
        if k == 'rec':
            return {f: s.eval(e, scope, env) for f, e in n[1]}
        if k == 'arr':
            return Table({'Value': s.eval(e, scope, env)} for e in n[1])
        if k == 'and':
            return tobool(s.eval(n[1], scope, env)) and tobool(s.eval(n[2], scope, env))
        if k == 'or':
            return tobool(s.eval(n[1], scope, env)) or tobool(s.eval(n[2], scope, env))
        if k == 'not':
            return not tobool(s.eval(n[1], scope, env))
        if k == 'neg':
            v = s.eval(n[1], scope, env)
            return None if v is None else -tonum(v)
        if k == 'bin': return s.binop(n[1], s.eval(n[2], scope, env), s.eval(n[3], scope, env))
        if k == 'dot': return s.dot(n, scope, env)
        if k == 'call': return s.call(n, scope, env)
        if k == 'as': raise PfxError('As outside function')
        raise PfxError('bad node ' + k)

    def dot(s, n, scope, env):
        base = n[1]; name = n[2]
        if base[0] == 'id':
            full = base[1] + '.' + name
            if full in ENUMS: return ENUMS[full]
            if base[1] in ('Color',): return Color((0, 0, 0, 1))
        b = s.eval(base, scope, env)
        if isinstance(b, tuple) and b and b[0] == 'ctrl':
            return s.prop(b[1], name)
        if isinstance(b, tuple) and b and b[0] == 'parent':
            c = s.ctrls[b[1]] if b[1] else None
            par = c.parent if c else None
            if par is None:
                if name in ('Width',): return float(s.width)
                if name in ('Height',): return float(s.height)
                raise PfxError('Parent.' + name)
            if name == 'TemplateWidth': return s.prop(par, 'TemplateWidth')
            if name == 'TemplateHeight': return s.prop(par, 'TemplateSize')
            return s.prop(par, name)
        if isinstance(b, Untyped):
            if isinstance(b.v, dict): return Untyped(b.v.get(name))
            if b.v is None: return Untyped(None)
            raise PfxError('untyped member access on non-object')
        if isinstance(b, dict):
            if name not in b:
                raise PfxError('record has no field %s (fields %s)' % (name, list(b)[:12]), 'Name')
            return b[name]
        if isinstance(b, list):
            return Table({'Value': (r.get(name) if isinstance(r, dict) else None)} for r in b) if True else None
        if b is None: return None
        raise PfxError('cannot access .%s on %r' % (name, type(b)))

    def binop(s, op, a, b):
        if op == '&': return (totext(a) or '') + (totext(b) or '')
        if op in ('+', '-', '*', '/', '^'):
            if a is None and b is None and op in ('+', '-'): return None
            x, y = tonum(a), tonum(b)
            x = 0.0 if x is None else x; y = 0.0 if y is None else y
            if op == '+': return x + y
            if op == '-': return x - y
            if op == '*': return x * y
            if op == '/':
                if y == 0: raise PfxError('division by zero', 'Div0')
                return x / y
            return x ** y
        if op in ('in', 'exactin'):
            if isinstance(b, list):
                vals = [r.get('Value') if isinstance(r, dict) and len(r) == 1 else r for r in b]
                if op == 'in' and isinstance(a, str):
                    return any(isinstance(v, str) and v.lower() == a.lower() for v in vals) or a in vals
                return any(s.eq(a, v) for v in vals)
            at, bt = totext(a) or '', totext(b) or ''
            return (at.lower() in bt.lower()) if op == 'in' else (at in bt)
        if op == '=': return s.eq(a, b)
        if op == '<>': return not s.eq(a, b)
        if isinstance(a, Untyped) or isinstance(b, Untyped):
            raise PfxError('compare untyped')
        if isinstance(a, str) or isinstance(b, str):
            if isinstance(a, (int, float)) or isinstance(b, (int, float)):
                a, b = tonum(a), tonum(b)
            else:
                a, b = a or '', b or ''
        elif isinstance(a, datetime.datetime) or isinstance(b, datetime.datetime):
            if a is None or b is None: return False
        else:
            a = 0.0 if a is None else tonum(a); b = 0.0 if b is None else tonum(b)
        return {'<': a < b, '>': a > b, '<=': a <= b, '>=': a >= b}[op]

    def eq(s, a, b):
        if isinstance(a, Untyped) or isinstance(b, Untyped):
            raise PfxError('compare untyped value; use Text()/Value()')
        if a is None and b is None: return True
        if a is None or b is None:
            return False
        if isinstance(a, bool) or isinstance(b, bool):
            return tobool(a) == tobool(b)
        if isinstance(a, (int, float)) and isinstance(b, (int, float)): return float(a) == float(b)
        if isinstance(a, (int, float)) or isinstance(b, (int, float)):
            try: return tonum(a) == tonum(b)
            except PfxError: return False
        if isinstance(a, dict) and isinstance(b, dict): return a == b
        return a == b

    # ---------------- table helpers
    def table(s, v, env=None):
        if isinstance(v, DSQuery): return v.materialize(s)
        if isinstance(v, tuple) and v and v[0] == 'ds':
            return DSQuery(s.sp, delegable=True).materialize(s)
        if v is None: return Table()
        if isinstance(v, dict): return Table([v])
        if isinstance(v, list): return v
        raise PfxError('not a table: %r' % (type(v),))

    def tab_arg(s, a, scope, env):
        """returns (alias, table-or-query)"""
        alias = None
        if a[0] == 'as': alias = a[2]; a = a[1]
        return alias, s.eval(a, scope, env)

    def rowscope(s, scope, rec, alias):
        return scope + [Scope(rec=rec, alias=alias)]

    # ---------------- functions
    def call(s, n, scope, env):
        fname, args = n[1], n[2]
        f = getattr(s, 'f_' + fname, None)
        if f is None: raise PfxError('unknown function ' + fname, 'Name')
        return f(args, scope, env)

    def ev(s, a, scope, env): return s.eval(a, scope, env)

    # control flow
    def f_If(s, a, sc, env):
        i = 0
        while i + 1 < len(a):
            if tobool(s.ev(a[i], sc, env)): return s.ev(a[i + 1], sc, env)
            i += 2
        return s.ev(a[i], sc, env) if i < len(a) else None
    def f_Switch(s, a, sc, env):
        v = s.ev(a[0], sc, env); i = 1
        while i + 1 < len(a):
            if s.eq(v, s.ev(a[i], sc, env)): return s.ev(a[i + 1], sc, env)
            i += 2
        return s.ev(a[i], sc, env) if i < len(a) else None
    def f_IfError(s, a, sc, env):
        i = 0
        while True:
            try:
                v = s.ev(a[i], sc, env)
            except PfxError as e:
                if i + 1 < len(a):
                    env2 = dict(env); env2['firsterror'] = e
                    return s.ev(a[i + 1], sc + [Scope(names={'FirstError': {'Message': e.msg, 'Kind': e.kind}})], env2)
                return None
            if i + 2 < len(a): i += 2; continue
            if i + 2 == len(a) - 1:
                return s.ev(a[-1], sc, env)
            return v
    def f_With(s, a, sc, env):
        rec = s.ev(a[0], sc, env)
        if not isinstance(rec, dict): raise PfxError('With needs record')
        return s.ev(a[1], sc + [Scope(names=dict(rec))], env)
    def f_Error(s, a, sc, env):
        r = s.ev(a[0], sc, env)
        raise PfxError(r.get('Message', 'error') if isinstance(r, dict) else totext(r))

    # scalar
    def f_Blank(s, a, sc, env): return None
    def f_IsBlank(s, a, sc, env): return isblank(s.ev(a[0], sc, env))
    def f_IsEmpty(s, a, sc, env): return len(s.table(s.ev(a[0], sc, env))) == 0
    def f_Coalesce(s, a, sc, env):
        for x in a:
            v = s.ev(x, sc, env)
            if not isblank(v): return v
        return None
    def f_Abs(s, a, sc, env):
        v = s.ev(a[0], sc, env); return None if v is None else abs(tonum(v))
    def f_Round(s, a, sc, env):
        v = tonum(s.ev(a[0], sc, env)) or 0.0; d = int(tonum(s.ev(a[1], sc, env)))
        q = 10 ** d; return math.floor(abs(v) * q + 0.5) / q * (1 if v >= 0 else -1)
    def f_RoundDown(s, a, sc, env):
        v = tonum(s.ev(a[0], sc, env)) or 0.0; d = int(tonum(s.ev(a[1], sc, env)))
        q = 10 ** d; return math.floor(abs(v) * q) / q * (1 if v >= 0 else -1)
    def f_RoundUp(s, a, sc, env):
        v = tonum(s.ev(a[0], sc, env)) or 0.0; d = int(tonum(s.ev(a[1], sc, env)))
        q = 10 ** d; return math.ceil(abs(v) * q - 1e-12) / q * (1 if v >= 0 else -1)
    def f_Mod(s, a, sc, env):
        x = tonum(s.ev(a[0], sc, env)); y = tonum(s.ev(a[1], sc, env)); return x - y * math.floor(x / y)
    def _agg(s, a, sc, env, fn):
        if len(a) >= 2 and a[0][0] in ('id', 'call', 'as', 'dot') and s._is_table_expr(a[0], sc, env) and len(a) == 2:
            alias, t = s.tab_arg(a[0], sc, env); t = s.table(t)
            vals = [s.ev(a[1], s.rowscope(sc, r, alias), env) for r in t]
            vals = [tonum(v) for v in vals if v is not None and v != '']
            return fn(vals) if vals else None
        vals = [s.ev(x, sc, env) for x in a]
        vals = [tonum(v) for v in vals if v is not None and v != '']
        return fn(vals) if vals else None
    def _is_table_expr(s, node, sc, env):
        try:
            v = s.ev(node[1] if node[0] == 'as' else node, sc, env)
        except PfxError:
            return False
        return isinstance(v, (list, DSQuery)) or (isinstance(v, tuple) and v and v[0] == 'ds')
    def f_Max(s, a, sc, env): return s._agg(a, sc, env, max)
    def f_Min(s, a, sc, env): return s._agg(a, sc, env, min)
    def f_Sum(s, a, sc, env):
        r = s._agg(a, sc, env, sum)
        return 0.0 if r is None else r
    def f_Value(s, a, sc, env):
        v = s.ev(a[0], sc, env)
        if v is None: return None
        if isinstance(v, Untyped):
            if v.v is None: return None
            if isinstance(v.v, bool): raise PfxError('Value(untyped bool)')
            if isinstance(v.v, (dict, list)): raise PfxError('Value(untyped object)')
        if isinstance(v, str) and v.strip() == '': return None
        return tonum(v)
    def f_Text(s, a, sc, env):
        v = s.ev(a[0], sc, env)
        if len(a) == 1:
            if isinstance(v, Untyped):
                if v.v is None: return None
                if isinstance(v.v, (dict, list)): raise PfxError('Text(untyped object)')
            return totext(v)
        f = s.ev(a[1], sc, env)
        loc = s.ev(a[2], sc, env) if len(a) > 2 else 'en-US'
        if isinstance(f, Enum):
            if f.name == 'DateTimeFormat.UTC':
                if not isinstance(v, datetime.datetime): raise PfxError('UTC fmt on non-date')
                return v.strftime('%Y-%m-%dT%H:%M:%S.000Z')
        if isinstance(v, datetime.datetime):
            return v.strftime({'hh:mm': '%H:%M', 'dd/mm/yyyy hh:mm': '%d/%m/%Y %H:%M'}.get(f, '%d/%m/%Y'))
        if v is None: return ''
        if isinstance(v, Untyped): v = tonum(v)
        return format_number(tonum(v), f, loc)
    def f_Boolean(s, a, sc, env):
        v = s.ev(a[0], sc, env)
        if isinstance(v, Untyped):
            if v.v is None: return None
            if isinstance(v.v, bool): return v.v
            if isinstance(v.v, str) and v.v.lower() in ('true', 'false'): return v.v.lower() == 'true'
            raise PfxError('Boolean(untyped)')
        return tobool(v)
    def f_Char(s, a, sc, env): return chr(int(tonum(s.ev(a[0], sc, env))))
    def f_Len(s, a, sc, env): return float(len(totext(s.ev(a[0], sc, env)) or ''))
    def f_Lower(s, a, sc, env): return (totext(s.ev(a[0], sc, env)) or '').lower()
    def f_Upper(s, a, sc, env): return (totext(s.ev(a[0], sc, env)) or '').upper()
    def f_Trim(s, a, sc, env): return re.sub(r' +', ' ', (totext(s.ev(a[0], sc, env)) or '').strip(' '))
    def f_Mid(s, a, sc, env):
        t = totext(s.ev(a[0], sc, env)) or ''; st = int(tonum(s.ev(a[1], sc, env)))
        if st < 1: raise PfxError('Mid start < 1')
        ln = int(tonum(s.ev(a[2], sc, env))) if len(a) > 2 else len(t)
        return t[st - 1:st - 1 + ln]
    def f_Find(s, a, sc, env):
        f = totext(s.ev(a[0], sc, env)) or ''; t = totext(s.ev(a[1], sc, env)) or ''
        st = int(tonum(s.ev(a[2], sc, env))) if len(a) > 2 else 1
        i = t.find(f, st - 1); return None if i < 0 else float(i + 1)
    def f_StartsWith(s, a, sc, env):
        return (totext(s.ev(a[0], sc, env)) or '').lower().startswith((totext(s.ev(a[1], sc, env)) or '').lower())
    def f_EndsWith(s, a, sc, env):
        return (totext(s.ev(a[0], sc, env)) or '').lower().endswith((totext(s.ev(a[1], sc, env)) or '').lower())
    def f_Substitute(s, a, sc, env):
        t = totext(s.ev(a[0], sc, env)) or ''; o = totext(s.ev(a[1], sc, env)) or ''; nw = totext(s.ev(a[2], sc, env)) or ''
        return t.replace(o, nw) if o else t
    def f_IsMatch(s, a, sc, env):
        t = totext(s.ev(a[0], sc, env)) or ''; p = totext(s.ev(a[1], sc, env)) or ''
        opt = s.ev(a[2], sc, env) if len(a) > 2 else None
        if opt == ENUMS['MatchOptions.Contains']: return re.search(p, t) is not None
        return re.fullmatch(p, t) is not None
    def f_IsNumeric(s, a, sc, env):
        try: tonum(s.ev(a[0], sc, env)); return True
        except PfxError: return False
    def f_Split(s, a, sc, env):
        t = totext(s.ev(a[0], sc, env)) or ''; d = totext(s.ev(a[1], sc, env))
        return Table({'Value': x} for x in t.split(d))
    def f_EncodeUrl(s, a, sc, env):
        from urllib.parse import quote
        return quote(totext(s.ev(a[0], sc, env)) or '', safe='')
    def f_GUID(s, a, sc, env):
        s.guid_n += 1
        return str(uuid.UUID(int=(hash(s.user) & 0xffffffff) << 64 | s.guid_n))
    def f_Now(s, a, sc, env): return s.now()
    def f_DateAdd(s, a, sc, env):
        d = s.ev(a[0], sc, env); n_ = tonum(s.ev(a[1], sc, env)); u = s.ev(a[2], sc, env)
        unit = {'TimeUnit.Minutes': 'minutes', 'TimeUnit.Seconds': 'seconds', 'TimeUnit.Days': 'days'}[u.name]
        return d + datetime.timedelta(**{unit: n_})
    def f_User(s, a, sc, env): return {'FullName': s.user, 'Email': s.user.replace(' ', '.') + '@x.com'}
    def f_RGBA(s, a, sc, env): return Color(tuple(tonum(s.ev(x, sc, env)) for x in a))
    def f_Sequence(s, a, sc, env):
        n_ = int(tonum(s.ev(a[0], sc, env)) or 0)
        return Table({'Value': float(i + 1)} for i in range(max(0, n_)))

    # JSON
    def to_json_val(s, v):
        if isinstance(v, Untyped): return v.v
        if isinstance(v, list): return [s.to_json_val(r if not (isinstance(r, dict) and list(r) == ['Value'] and False) else r) for r in v]
        if isinstance(v, dict): return {k: s.to_json_val(x) for k, x in v.items()}
        if isinstance(v, float) and v == int(v) and abs(v) < 1e15: return int(v)
        if isinstance(v, datetime.datetime): return v.strftime('%Y-%m-%dT%H:%M:%S.000Z')
        if isinstance(v, Color): raise PfxError('JSON of color')
        return v
    def f_JSON(s, a, sc, env):
        v = s.ev(a[0], sc, env)
        if isinstance(v, DSQuery): v = s.table(v)
        return json.dumps(s.to_json_val(v), ensure_ascii=False, separators=(',', ':'))
    def f_ParseJSON(s, a, sc, env):
        t = totext(s.ev(a[0], sc, env))
        if t is None or t == '': raise PfxError('ParseJSON of blank')
        try: return Untyped(json.loads(t))
        except Exception as e: raise PfxError('ParseJSON: ' + str(e)[:60])
    def f_Table(s, a, sc, env):
        if len(a) == 1:
            v = s.ev(a[0], sc, env)
            if isinstance(v, Untyped):
                if not isinstance(v.v, list): raise PfxError('Table(untyped non-array)')
                return Table({'Value': Untyped(x)} for x in v.v)
            if isinstance(v, dict): return Table([v])
            if isinstance(v, list): return Table(v)
        return Table(s.ev(x, sc, env) for x in a)

    # tables
    def f_CountRows(s, a, sc, env): return float(len(s.table(s.ev(a[0], sc, env))))
    def f_First(s, a, sc, env):
        t = s.table(s.ev(a[0], sc, env)); return dict(t[0]) if t else None
    def f_Last(s, a, sc, env):
        t = s.table(s.ev(a[0], sc, env)); return dict(t[-1]) if t else None
    def f_FirstN(s, a, sc, env):
        t = s.table(s.ev(a[0], sc, env)); n_ = int(tonum(s.ev(a[1], sc, env))) if len(a) > 1 else 1
        return Table(t[:n_])
    def f_LastN(s, a, sc, env):
        t = s.table(s.ev(a[0], sc, env)); n_ = int(tonum(s.ev(a[1], sc, env)))
        return Table(t[-n_:] if n_ else [])
    def f_Index(s, a, sc, env):
        t = s.table(s.ev(a[0], sc, env)); i = int(tonum(s.ev(a[1], sc, env)))
        if i < 1 or i > len(t): raise PfxError('Index out of range')
        return dict(t[i - 1])
    def f_Filter(s, a, sc, env):
        alias, src = s.tab_arg(a[0], sc, env)
        if isinstance(src, tuple) and src and src[0] == 'ds':
            pred = a[1] if len(a) == 2 else ('and', a[1], a[2])
            return DSQuery(s.sp, pred, (sc, env, alias), delegable=s.delegable(pred, alias, sc, env))
        if isinstance(src, DSQuery):
            src = src.materialize(s)
        t = s.table(src)
        out = Table()
        for r in t:
            ok = True
            for p in a[1:]:
                if not tobool(s.ev(p, s.rowscope(sc, r, alias), env)): ok = False; break
            if ok: out.append(r)
        return out
    def f_LookUp(s, a, sc, env):
        alias, src = s.tab_arg(a[0], sc, env)
        if isinstance(src, tuple) and src and src[0] == 'ds':
            q = DSQuery(s.sp, a[1], (sc, env, alias), delegable=s.delegable(a[1], alias, sc, env))
            t = q.materialize(s)
            r = t[0] if t else None
        else:
            t = s.table(src); r = None
            for x in t:
                if tobool(s.ev(a[1], s.rowscope(sc, x, alias), env)): r = x; break
        if r is None: return None
        if len(a) > 2: return s.ev(a[2], s.rowscope(sc, r, alias), env)
        return dict(r)
    def f_CountIf(s, a, sc, env):
        alias, src = s.tab_arg(a[0], sc, env); t = s.table(src)
        return float(sum(1 for r in t if all(tobool(s.ev(p, s.rowscope(sc, r, alias), env)) for p in a[1:])))
    def f_ForAll(s, a, sc, env):
        alias, src = s.tab_arg(a[0], sc, env); t = list(s.table(src))
        out = Table()
        for r in t:
            v = s.ev(a[1], s.rowscope(sc, r, alias), env)
            if v is not None: out.append(v if isinstance(v, dict) else {'Value': v})
        return out
    def f_AddColumns(s, a, sc, env):
        alias, src = s.tab_arg(a[0], sc, env); t = s.table(src)
        out = Table()
        for r in t:
            nr = dict(r)
            for i in range(1, len(a), 2):
                cn = a[i]
                cname = cn[1] if cn[0] in ('id', 'str') else None
                if cname is None: raise PfxError('AddColumns name')
                nr[cname] = s.ev(a[i + 1], s.rowscope(sc, r, alias), env)
            out.append(nr)
        return out
    def f_ShowColumns(s, a, sc, env):
        t = s.table(s.ev(a[0], sc, env)); cols = [x[1] for x in a[1:]]
        out = Table()
        for r in t:
            for c in cols:
                if c not in r: raise PfxError('ShowColumns: no column ' + c)
            out.append({c: r[c] for c in cols})
        return out
    def f_DropColumns(s, a, sc, env):
        t = s.table(s.ev(a[0], sc, env)); cols = [x[1] for x in a[1:]]
        return Table({k: v for k, v in r.items() if k not in cols} for r in t)
    def f_SortByColumns(s, a, sc, env):
        src = s.ev(a[0], sc, env)
        sorts = []
        i = 1
        while i < len(a):
            c = s.ev(a[i], sc, env); o = s.ev(a[i + 1], sc, env) if i + 1 < len(a) else ENUMS['SortOrder.Ascending']
            sorts.append((c, o == ENUMS['SortOrder.Descending'])); i += 2
        if isinstance(src, tuple) and src and src[0] == 'ds':
            src = DSQuery(s.sp)
        if isinstance(src, DSQuery):
            deleg = src.delegable and all(c in DELEGABLE_NUM or c in DELEGABLE_TEXT for c, _ in sorts)
            return DSQuery(src.sp, src.pred, src.pred_env, sorts, deleg)
        t = s.table(src)
        for c, _ in sorts:
            if t and c not in t[0]: raise PfxError('SortByColumns: no column ' + str(c))
        return Table(sort_rows(t, sorts))
    def f_Sort(s, a, sc, env):
        alias, src = s.tab_arg(a[0], sc, env); t = s.table(src)
        desc = len(a) > 2 and s.ev(a[2], sc, env) == ENUMS['SortOrder.Descending']
        keyed = [(sort_key_val(s.ev(a[1], s.rowscope(sc, r, alias), env)), i, r) for i, r in enumerate(t)]
        keyed.sort(key=lambda x: x[0], reverse=desc)
        return Table(r for _, _, r in keyed)
    def f_Distinct(s, a, sc, env):
        alias, src = s.tab_arg(a[0], sc, env); t = s.table(src)
        seen = []; out = Table()
        for r in t:
            v = s.ev(a[1], s.rowscope(sc, r, alias), env)
            if v not in seen: seen.append(v); out.append({'Value': v})
        return out
    def f_Concat(s, a, sc, env):
        alias, src = s.tab_arg(a[0], sc, env); t = s.table(src)
        sep = totext(s.ev(a[2], sc, env)) if len(a) > 2 else ''
        return sep.join((totext(s.ev(a[1], s.rowscope(sc, r, alias), env)) or '') for r in t)
    def f_Defaults(s, a, sc, env): return {}

    # behavior
    def _colname(s, node):
        if node[0] != 'id' or not node[1].startswith('col'): raise PfxError('collection expected')
        return node[1]
    def _rows_of(s, v):
        if isinstance(v, DSQuery): v = v.materialize(s)
        if isinstance(v, dict): return [dict(v)]
        if isinstance(v, list): return [dict(r) for r in v]
        if v is None: return []
        return [{'Value': v}]
    def f_Set(s, a, sc, env):
        nm = a[0][1]
        v = s.ev(a[1], sc, env)
        if isinstance(v, DSQuery): v = v.materialize(s)
        s.globals[nm] = v; return True
    def f_ClearCollect(s, a, sc, env):
        nm = s._colname(a[0]); rows = []
        for x in a[1:]: rows += s._rows_of(s.ev(x, sc, env))
        s.cols[nm] = Table(rows); return s.cols[nm]
    def f_Collect(s, a, sc, env):
        nm = s._colname(a[0]); rows = []
        for x in a[1:]: rows += s._rows_of(s.ev(x, sc, env))
        s.cols.setdefault(nm, Table()).extend(rows); return s.cols[nm]
    def f_Clear(s, a, sc, env):
        s.cols[s._colname(a[0])] = Table(); return True
    def f_RemoveIf(s, a, sc, env):
        nm = s._colname(a[0]); t = s.cols.get(nm, Table())
        s.cols[nm] = Table(r for r in t if not tobool(s.ev(a[1], s.rowscope(sc, r, None), env))); return True
    def f_UpdateIf(s, a, sc, env):
        nm = s._colname(a[0]); t = s.cols.get(nm, Table())
        for r in t:
            if tobool(s.ev(a[1], s.rowscope(sc, r, None), env)):
                ch = s.ev(a[2], s.rowscope(sc, r, None), env); r.update(ch)
        return True
    def f_Patch(s, a, sc, env):
        if a[0][0] == 'id' and a[0][1] == 'DashboardPOC_Data':
            base = s.ev(a[1], sc, env)
            ch = {}
            for x in a[2:]: ch.update(s.ev(x, sc, env))
            if base == {} or base is None and a[1][0] == 'call' and a[1][1] == 'Defaults':
                return s.sp.insert(ch)
            if base is None: raise PfxError('Patch: base record not found')
            return s.sp.update(base['ID'], ch)
        base = s.ev(a[0], sc, env)
        if isinstance(base, dict):
            r = dict(base)
            for x in a[1:]: r.update(s.ev(x, sc, env))
            return r
        raise PfxError('Patch on collection not modeled')
    def f_Refresh(s, a, sc, env): return True
    def f_Notify(s, a, sc, env):
        s.notes.append((totext(s.ev(a[1], sc, env)) if len(a) > 1 else '', totext(s.ev(a[0], sc, env)))); return True
    def f_Reset(s, a, sc, env):
        nm = a[0][1]
        if nm == 'Self': nm = env.get('ctrl')
        c = s.ctrls[nm]; c.state.pop('text', None); return True
    def f_Select(s, a, sc, env):
        s.queue.append(a[0][1]); return True
    def f_Copy(s, a, sc, env):
        s.clipboard = totext(s.ev(a[0], sc, env)); return True
    def f_Launch(s, a, sc, env):
        s.launched.append(totext(s.ev(a[0], sc, env))); return True
    def f_Print(s, a, sc, env): return True

    # ---------------- delegation analysis (SharePoint)
    def delegable(s, pred, alias, sc, env):
        def rowfree(n):
            # true if node does not reference the row
            if n[0] == 'id':
                if alias and n[1] == alias: return False
                if n[1].startswith('field_') or n[1] in ('ID', 'Title', 'AuditNote', 'Created', 'AuditStatus', 'EvidenceUrl'):
                    return False
                return True
            if n[0] in ('num', 'str', 'bool'): return True
            if n[0] == 'dot': return rowfree(n[1])
            if n[0] == 'call': return all(rowfree(x) for x in n[2])
            if n[0] in ('bin',): return rowfree(n[2]) and rowfree(n[3])
            if n[0] in ('and', 'or'): return rowfree(n[1]) and rowfree(n[2])
            if n[0] in ('not', 'neg'): return rowfree(n[1])
            if n[0] == 'rec': return all(rowfree(e) for _, e in n[1])
            if n[0] == 'arr': return all(rowfree(e) for e in n[1])
            if n[0] == 'chain': return all(rowfree(e) for e in n[1])
            return False
        def col(n):
            if n[0] == 'id' and (n[1].startswith('field_') or n[1] in ('ID', 'Title')): return n[1]
            if n[0] == 'dot' and alias and n[1][0] == 'id' and n[1][1] == alias: return n[2]
            return None
        def ok(n):
            if n[0] in ('and', 'or'): return ok(n[1]) and ok(n[2])
            if n[0] == 'bin' and n[1] in ('=', '<', '>', '<=', '>=', '<>'):
                c = col(n[2])
                if c and rowfree(n[3]):
                    if c == 'ID': return n[1] == '='
                    if c in DELEGABLE_NUM: return True
                    if c in DELEGABLE_TEXT: return n[1] in ('=', '<>')
                return False
            return False
        return ok(pred)
