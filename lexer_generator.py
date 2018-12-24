import sys

import automaton
import regexp

def simulate(inp):
    state = dfa.start_state
    actions = None
    last_final = -1
    prev_state = None

    capture_start = -1

    pos = 0
    while pos < len(inp):
        ch = inp[pos]
        print ch, state
        mapped = im[ord(ch)]
        prev_state = state
        state = dfa.edges[state].lookup(mapped)
        print ' now in', state

        if state != prev_state:
            if regexp.START_CAPTURE in dfa.labels[state]:
                capture_start = pos + 1
            elif regexp.END_CAPTURE in dfa.labels[prev_state]:
                print 'CAPTURE:', prev_state, state, capture_start, pos, inp[capture_start : pos]

        if state in dfa.final_states:
            actions = dfa.labels[state]
            last_final = pos

        if state not in non_end_states:
            if last_final >= 0:
                print 'Got token. Actions =', actions
                actions = None
                state = dfa.start_state
                pos = last_final + 1
                last_final = -1
            else:
                print 'Syntax error at', pos
                return
        else:
            pos += 1

    print state

spec = {}
execfile(sys.argv[1], spec)

macros = spec["MACROS"]
rules = spec["RULES"]

nfa = automaton.Automaton()
start = 0
nfa.add_state(0)
nfa.set_start_state(0)
finals = set()
for (n, (re, action)) in enumerate(rules):
    for macro in macros:
        re = re.replace("{" + macro + "}", macros[macro])

    print (re, action)

    r = regexp.RegExp(re)
    (start, final) = r.add_to_nfa(nfa)

    nfa.add_edge(0, automaton.EPSILON_RANGE, start)
    nfa.label_state(final, n)
    finals.add(final)

nfa.set_final_states(finals)
dfa = nfa.construct_dfa(0, 256)
print dfa
#check = dfa.verify_dfa_label_consistency(nfa, set([regexp.START_CAPTURE, regexp.END_CAPTURE]))
check = None
if check:
    print 'Label inconsistency!'
    print 'NFA'
    print nfa
    print 'DFA'
    print dfa
    print 'Check failure'
    print check
    sys.exit(1)
dfa = dfa.renumber()
print dfa
(im, dfa) = dfa.construct_input_mapped_dfa(0, 256)
non_end_states = dfa.states_reaching_finals()
print 'non-end', non_end_states

#print im
#print dfa
#print im

simulate(sys.argv[2])
