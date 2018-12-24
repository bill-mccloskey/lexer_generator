import automaton
import rangemap

# In input ranges, we treat -1 as epsilon.

END = 0
EPSILON = automaton.EPSILON
EPSILON_RANGE = automaton.EPSILON_RANGE

START_CAPTURE = -2
END_CAPTURE = -1

state_num = 0
def new_state(nfa):
    global state_num
    state_num = state_num + 1
    nfa.add_state(state_num)
    return state_num

class Node(object):
    pass

class EmptyString(Node):
    def __init__(self):
        pass

    def __str__(self):
        return "empty"

    def construct_nfa(self, nfa):
        s1 = new_state(nfa)
        s2 = new_state(nfa)
        nfa.add_edge(s1, EPSILON_RANGE, s2)
        return (s1, s2)

class CharRange(Node):
    def __init__(self, range):
        self.range = range

    def __str__(self):
        return str(self.range)

    def construct_nfa(self, nfa):
        s1 = new_state(nfa)
        s2 = new_state(nfa)
        nfa.add_edge(s1, self.range, s2)
        return (s1, s2)

class Concat(Node):
    def __init__(self, n1, n2):
        self.n1 = n1
        self.n2 = n2

    def __str__(self):
        return 'Concat(%s,%s)' % (str(self.n1), str(self.n2))

    def construct_nfa(self, nfa):
        (s1, f1) = self.n1.construct_nfa(nfa)
        (s2, f2) = self.n2.construct_nfa(nfa)
        nfa.add_edge(f1, EPSILON_RANGE, s2)
        return (s1, f2)

class Or(Node):
    def __init__(self, n1, n2):
        self.n1 = n1
        self.n2 = n2

    def __str__(self):
        return 'Or(%s,%s)' % (str(self.n1), str(self.n2))

    def construct_nfa(self, nfa):
        s = new_state(nfa)
        (s1, f1) = self.n1.construct_nfa(nfa)
        (s2, f2) = self.n2.construct_nfa(nfa)
        f = new_state(nfa)
        nfa.add_edge(s, EPSILON_RANGE, s1)
        nfa.add_edge(s, EPSILON_RANGE, s2)
        nfa.add_edge(f1, EPSILON_RANGE, f)
        nfa.add_edge(f2, EPSILON_RANGE, f)
        return (s, f)

class Star(Node):
    def __init__(self, inner):
        self.inner = inner

    def __str__(self):
        return 'Star(%s)' % (str(self.inner))

    def construct_nfa(self, nfa):
        sf = new_state(nfa)
        (s, f) = self.inner.construct_nfa(nfa)
        nfa.add_edge(sf, EPSILON_RANGE, s)
        nfa.add_edge(f, EPSILON_RANGE, sf)
        return (sf, sf)

class Capture(Node):
    def __init__(self, inner):
        self.inner = inner

    def __str__(self):
        return 'Capture(%s)' % (str(self.inner))

    def construct_nfa(self, nfa):
        s = new_state(nfa)
        f = new_state(nfa)
        nfa.label_state(s, START_CAPTURE)
        nfa.label_state(f, END_CAPTURE)
        (si, fi) = self.inner.construct_nfa(nfa)
        nfa.add_edge(s, EPSILON_RANGE, si)
        nfa.add_edge(fi, EPSILON_RANGE, f)
        return (s, f)

class RegExp(object):
    def __init__(self, re):
        self.input = list(re) + [END]
        self.root = self.parse_regexp()

    def __str__(self):
        return str(self.root)

    def syntax_error(self):
        print self.input
        raise AssertionError

    def get_input(self):
        r = self.input[0]
        self.input = self.input[1:]
        return r

    def peek_input(self):
        return self.input[0]

    def parse_regexp(self):
        n1 = self.parse_concat()
        while True:
            n2 = self.parse_rest_or()
            if n2: n1 = Or(n1, n2)
            else: break
        return n1

    def parse_rest_or(self):
        if self.peek_input() == '|':
            self.get_input()
            return self.parse_concat()
        else:
            return None

    def parse_concat(self):
        n1 = self.parse_star()
        while True:
            n2 = self.parse_rest_concat()
            if n2: n1 = Concat(n1, n2)
            else: break
        return n1

    # FIXME: This is broken for "12|3"
    def parse_rest_concat(self):
        if self.peek_input() in ['*', ')', '}', '|', '?', END]:
            return None
        else:
            return self.parse_star()

    def parse_star(self):
        n1 = self.parse_base()
        extra = self.parse_rest_star()
        if extra == '*': return Star(n1)
        elif extra == '?': return Or(EmptyString(), n1)
        else: return n1

    def parse_rest_star(self):
        if self.peek_input() == '*':
            self.get_input()
            return "*"
        elif self.peek_input() == '?':
            self.get_input()
            return "?"
        else:
            return None

    def parse_base(self):
        ch = self.peek_input()
        if ch == '(':
            self.get_input()
            n = self.parse_regexp()
            assert(self.get_input() == ')')
            return Capture(n)
        elif ch == '{':
            self.get_input()
            n = self.parse_regexp()
            assert(self.get_input() == '}')
            return n
        elif ch == '.':
            self.get_input()
            return CharRange(rangemap.Range(0, 256))
        elif ch == '[':
            self.get_input()
            negate = False
            if self.peek_input() == '^':
                self.get_input()
                negate = True

            a = self.parse_byte()
            if self.peek_input() == '-':
                self.get_input()
                b = self.parse_byte()
            else:
                b = a

            assert(self.get_input() == ']')

            if negate:
                return Or(CharRange(rangemap.Range(0, a)), CharRange(rangemap.Range(b + 1, 256)))
            else:
                return CharRange(rangemap.Range(a, b + 1))
        else:
            c = self.parse_byte()
            return CharRange(rangemap.Range(c, c + 1))

    def parse_byte(self):
        ch = self.get_input()
        if ch == '\\':
            assert(self.get_input() == 'x')
            h1 = self.get_input()
            h2 = self.get_input()
            return int(h1 + h2, 16)
        elif ch in ['*', '|', '(', ')', '{', '}', '?']:
            print ch
            self.syntax_error()
        else:
            return ord(ch)

    def construct_nfa(self):
        nfa = automaton.Automaton()
        (start, final) = self.root.construct_nfa(nfa)
        nfa.set_start_state(start)
        nfa.set_final_states(set([final]))
        return nfa

    def add_to_nfa(self, nfa):
        return self.root.construct_nfa(nfa)

if __name__ == '__main__':
    import sys
    re = RegExp(sys.argv[1])
    print re

    nfa = re.construct_nfa()
    dfa = nfa.construct_dfa(0, 256)
    print nfa
    print dfa
