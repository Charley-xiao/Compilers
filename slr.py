import logging

def setup_logger():
    logging.basicConfig(level=logging.DEBUG, format='%(message)s')

# Augmented grammar with productions stored as tuples of symbols
cfg = {
    "S'": [('S',)],  # Augmented start symbol
    'S': [('S', 'A'), ('S', 'B'), ('a',)],
    'A': [('S', '+')],
    'B': [('S', '-')]
}

def is_non_terminal(symbol):
    return symbol.isupper() or symbol == "S'"

def is_terminal(symbol):
    return not is_non_terminal(symbol)

class SLRParser:
    def __init__(self, cfg):
        self.cfg = cfg
        self.first = {}
        self.follow = {}
        self.states = []
        self.transitions = {}
        self.action = {}
        self.goto = {}
        self.build_first()
        self.build_follow()
        self.build_states()
        self.build_action_goto()

    def build_first(self):
        self.first = {symbol: set() for symbol in self.cfg}
        for symbol in self.cfg:
            self.build_first_for_symbol(symbol)

    def build_first_for_symbol(self, symbol):
        for production in self.cfg[symbol]:
            for sym in production:
                if is_terminal(sym):
                    self.first[symbol].add(sym)
                    break
                elif sym != symbol:  # Avoid immediate left recursion
                    self.build_first_for_symbol(sym)
                    self.first[symbol].update(self.first[sym] - {'ε'})
                    if 'ε' not in self.first[sym]:
                        break
                else:
                    break

    def build_follow(self):
        self.follow = {symbol: set() for symbol in self.cfg}
        self.follow["S'"] = {'$'}
        changed = True
        while changed:
            changed = False
            for left in self.cfg:
                for production in self.cfg[left]:
                    follow_temp = self.follow[left]
                    for i in range(len(production)-1, -1, -1):
                        sym = production[i]
                        if is_non_terminal(sym):
                            if self.follow[sym] != self.follow[sym] | follow_temp:
                                self.follow[sym] |= follow_temp
                                changed = True
                            if 'ε' in self.first[sym]:
                                follow_temp = follow_temp | (self.first[sym] - {'ε'})
                            else:
                                follow_temp = self.first[sym]
                        else:
                            follow_temp = {sym}

    def build_closure(self, items):
        closure = set(items)
        while True:
            new_items = set()
            for (left, production, dot) in closure:
                if dot < len(production):
                    symbol = production[dot]
                    if is_non_terminal(symbol):
                        for prod in self.cfg[symbol]:
                            new_item = (symbol, prod, 0)
                            if new_item not in closure:
                                new_items.add(new_item)
            if not new_items:
                break
            closure.update(new_items)
        return closure

    def build_goto(self, state, symbol):
        goto = set()
        for (left, production, dot) in state:
            if dot < len(production) and production[dot] == symbol:
                goto.add((left, production, dot + 1))
        return self.build_closure(goto)

    def build_states(self):
        logging.info('=========== Building states... ===========')
        start_item = ("S'", self.cfg["S'"][0], 0)
        start_closure = self.build_closure({start_item})
        self.states.append(start_closure)
        logging.info(f'State 0: {start_closure}')
        states_added = True
        while states_added:
            states_added = False
            for i, state in enumerate(self.states):
                logging.info(f'Processing state {i}...')
                symbols = set()
                for (left, production, dot) in state:
                    logging.info(f'Item: {left} -> {" ".join(production[:dot])}.{" ".join(production[dot:])}')
                    if dot < len(production):
                        logging.info(f'Next symbol: {production[dot]}')
                        symbols.add(production[dot])
                logging.info(f'Symbols: {symbols}')
                for symbol in symbols:
                    logging.info(f'Processing symbol {symbol}...')
                    goto_state = self.build_goto(state, symbol)
                    logging.info(f'Goto state: {goto_state}')
                    if goto_state and goto_state not in self.states:
                        logging.info(f'Adding state {len(self.states)}: {goto_state}')
                        self.states.append(goto_state)
                        states_added = True
                    self.transitions[(i, symbol)] = self.states.index(goto_state)

    def build_action_goto(self):
        for i, state in enumerate(self.states):
            for (left, production, dot) in state:
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
                        for terminal in self.follow[left]:
                            self.action[(i, terminal)] = ('r', (left, production))

    def parse(self, string):
        stack = [0]
        input_string = list(string) + ['$']
        index = 0
        while True:
            state = stack[-1]
            symbol = input_string[index]
            action = self.action.get((state, symbol))
            if action is None:
                print(f'Error: No action for state {state}, symbol {symbol}')
                return None
            op, val = action
            if op == 's':
                stack.append(val)
                index += 1
                print(f'Shift to {val}')
            elif op == 'r':
                left, production = val
                for _ in production:
                    stack.pop()
                state = stack[-1]
                goto_state = self.goto.get((state, left))
                if goto_state is None:
                    print(f'Error: No goto for state {state}, symbol {left}')
                    return None
                stack.append(goto_state)
                print(f'Reduce by {left} -> {" ".join(production)}')
            elif op == 'acc':
                print('Accepted')
                return True

    def print_tables(self):
        logging.info('First:')
        for symbol, first in self.first.items():
            logging.info(f'{symbol}: {first}')
        logging.info('Follow:')
        for symbol, follow in self.follow.items():
            logging.info(f'{symbol}: {follow}')
        logging.info('States:')
        for i, state in enumerate(self.states):
            str_state = ''
            for item in state:
                str_state += f'[{item[0]}->{" ".join(item[1][:item[2]])}.{" ".join(item[1][item[2]:])}], '
            logging.info(f'{i}: {str_state}')
        logging.info('Transitions:')
        for (i, symbol), s in self.transitions.items():
            logging.info(f'{i} --{symbol}--> {s}')
        logging.info('Action:')
        for (i, symbol), (op, val) in self.action.items():
            logging.info(f'{i}, {symbol}: {op} {val}')
        logging.info('Goto:')
        for (i, symbol), s in self.goto.items():
            logging.info(f'{i}, {symbol}: {s}')

if __name__ == '__main__':
    setup_logger()
    parser = SLRParser(cfg)
    parser.print_tables()
    parser.parse('aaaa+++')
