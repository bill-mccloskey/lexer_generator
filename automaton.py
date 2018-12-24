import rangemap

EPSILON = -1
EPSILON_RANGE = rangemap.Range(EPSILON, EPSILON + 1)

class Automaton(object):
    def __init__(self):
        self.states = set()
        self.edges = {}  # maps state -> RangeMap[input_range -> state]
        self.final_states = set()
        self.start_state = None
        self.labels = {}

    def __str__(self):
        r = 'Edges:\n'
        for (s1, rm) in self.edges.items():
            for (range, s2) in rm.get_entries():
                r += '%s --%s--> %s\n' % (str(s1), str(range), str(s2))

        r += 'Start: %s\n' % (str(self.start_state))
        r += 'Final: %s\n' % (str(self.final_states))
        r += 'Labels: %s' % (str(self.labels))
        return r

    def set_start_state(self, start):
        self.start_state = start

    def set_final_states(self, finals):
        self.final_states = finals

    def has_state(self, name):
        return name in self.states

    def add_state(self, name):
        self.states.add(name)
        self.edges[name] = rangemap.RangeMap()
        self.labels[name] = set()

    def set_labels(self, name, labels):
        self.labels[name] |= labels

    def label_state(self, name, label):
        self.labels[name].add(label)

    def add_edge(self, src, range, dst):
        rm = self.edges[src]
        rm.set(range, dst)

    def epsilon_close(self, states):
        new_states = set(states)
        for s in states:
            rm = self.edges[s]
            for (range, s2) in rm.get_entries():
                if range.start == EPSILON:
                    new_states.add(s2)

        if new_states == states:
            return frozenset(states)
        else:
            return self.epsilon_close(new_states)

    def collect_labels(self, states):
        labels = set()
        for s in states:
            labels |= self.labels[s]
        return labels

    def construct_dfa(self, min_value, max_value):
        dfa = Automaton()
        start = self.epsilon_close([self.start_state])
        dfa.add_state(start)
        dfa.set_start_state(start)
        dfa.set_labels(start, self.collect_labels(start))
        queue = [start]
        while queue:
            state = queue.pop()

            rm = rangemap.RangeMap()
            for s in state:
                rm.add(self.edges[s])
            rm = rm.canonicalize(min_value, max_value)
            for (range, state2) in rm.get_entries():
                state2 = self.epsilon_close(state2)
                if not dfa.has_state(state2):
                    dfa.add_state(state2)
                    dfa.set_labels(state2, self.collect_labels(state2))
                    queue.append(state2)
                dfa.add_edge(state, range, state2)

        finals = set()
        for state in dfa.states:
            for s in state:
                if s in self.final_states:
                    finals.add(state)
                    break
        dfa.set_final_states(finals)
        return dfa

    def construct_input_mapped_dfa(self, min_value, max_value):
        input_map = {}
        for inp in range(min_value, max_value):
            input_map[inp] = set()
        for (state1, rm) in self.edges.items():
            for (r, state2) in rm.get_entries():
                for inp in range(r.start, r.end):
                    input_map[inp].add((state1, state2))

        gen = -1
        numbering = {}
        examples = {}
        for (inp, transitions) in input_map.items():
            transitions = frozenset(transitions)
            if transitions not in numbering:
                gen += 1
                numbering[transitions] = gen
                examples[gen] = inp

        for (inp, transitions) in input_map.items():
            transitions = frozenset(transitions)
            input_map[inp] = numbering[transitions]

        new_dfa = Automaton()
        new_dfa.states = self.states
        new_dfa.start_state = self.start_state
        new_dfa.final_states = self.final_states
        new_dfa.labels = self.labels

        for (state1, rm) in self.edges.items():
            rmp = rangemap.RangeMap()
            new_dfa.edges[state1] = rmp
            for (r, state2) in rm.get_entries():
                has = {}
                for inp in range(r.start, r.end):
                    n = input_map[inp]
                    if n not in has:
                        has[n] = True
                        rmp.set(rangemap.Range(n, n + 1), state2)

        return (input_map, new_dfa)

    def renumber(self):
        gen = -1
        state_to_num = {}
        result = Automaton()
        for state in self.states:
            gen += 1
            state_to_num[state] = gen
            result.add_state(gen)

        result.set_start_state(state_to_num[self.start_state])

        finals = set()
        for state in self.final_states:
            finals.add(state_to_num[state])
        result.set_final_states(finals)

        for (state, label) in self.labels.items():
            result.set_labels(state_to_num[state], label)

        for (state1, rm) in self.edges.items():
            for (r, state2) in rm.get_entries():
                result.add_edge(state_to_num[state1], r, state_to_num[state2])

        return result

    def reachable_from(self, state):
        reach = set()
        while True:
            new_reach = reach.copy()
            for state in reach | set([state]):
                rm = self.edges[state]
                for (r, state2) in rm.get_entries():
                    new_reach.add(state2)

            if new_reach == reach:
                break
            else:
                reach = new_reach
        return reach

    # Returns the set of states that, via at least one edge, can reach a final state.
    def states_reaching_finals(self):
        result = set()
        for state in self.states:
            reach = self.reachable_from(state)
            if reach & self.final_states:
                result.add(state)
        return result

    # Checks that, for every label L in labels_to_check, if we have a state is
    # labeled with L, then all the NFA states it maps to are labeled with L.
    def verify_dfa_label_consistency(self, nfa, labels_to_check):
        for state in self.states:
            labels = self.labels[state]
            check = labels_to_check & labels
            for label in check:
                for s in state:
                    nfa_labels = nfa.labels[s]
                    if label not in nfa_labels:
                        return (state, s, label)

        return None
