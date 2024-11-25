import logging
from .SLR import SLRParser
from .symbols import is_terminal, is_non_terminal

class CLRParser(SLRParser):
    def build_closure(self, items):
        closure = set(items)
        while True:
            new_items = set()
            for (left, production, dot, lookahead) in closure:
                if dot < len(production):
                    symbol = production[dot]
                    if is_non_terminal(symbol):
                        for prod in self.cfg[symbol]:
                            first_of_rest = self.first_of_sequence(production[dot + 1:] + (lookahead,))
                            for terminal in first_of_rest:
                                new_item = (symbol, prod, 0, terminal)
                                if new_item not in closure:
                                    new_items.add(new_item)
            if not new_items:
                break
            closure.update(new_items)
        return closure

    def first_of_sequence(self, sequence):
        result = set()
        for symbol in sequence:
            if is_terminal(symbol):
                result.add(symbol)
                break
            result.update(self.first[symbol] - {'ε'})
            if 'ε' not in self.first[symbol]:
                break
        else:
            result.add('ε')
        return result

    def build_goto(self, state, symbol):
        goto = set()
        for (left, production, dot, lookahead) in state:
            if dot < len(production) and production[dot] == symbol:
                goto.add((left, production, dot + 1, lookahead))
        return self.build_closure(goto)

    def build_states(self):
        logging.debug('=========== Building states... ===========')
        start_item = ("S'", self.cfg["S'"][0], 0, '$')
        start_closure = self.build_closure({start_item})
        self.states.append(start_closure)
        logging.debug(f'State 0: {start_closure}')
        states_added = True
        while states_added:
            states_added = False
            for i, state in enumerate(self.states):
                logging.debug(f'Processing state {i}...')
                symbols = set()
                for (left, production, dot, lookahead) in state:
                    if dot < len(production):
                        symbols.add(production[dot])
                for symbol in symbols:
                    goto_state = self.build_goto(state, symbol)
                    if goto_state and goto_state not in self.states:
                        self.states.append(goto_state)
                        states_added = True
                    self.transitions[(i, symbol)] = self.states.index(goto_state)

    def build_action_goto(self):
        for i, state in enumerate(self.states):
            for (left, production, dot, lookahead) in state:
                if dot < len(production):
                    symbol = production[dot]
                    if is_terminal(symbol):
                        s = self.transitions.get((i, symbol))
                        if s is not None:
                            self.action[(i, symbol)] = ('s', s)
                    else:
                        s = self.transitions.get((i, symbol))
                        if s is not None:
                            self.goto[(i, symbol)] = s
                else:
                    if left == "S'":
                        self.action[(i, '$')] = ('acc', None)
                    else:
                        if lookahead in self.follow[left]:
                            self.action[(i, lookahead)] = ('r', (left, production))