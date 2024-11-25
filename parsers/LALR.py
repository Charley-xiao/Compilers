import logging 
from .symbols import is_terminal, is_non_terminal
from .CLR import CLRParser

class LALRParser(CLRParser):
    def __init__(self, cfg):
        super().__init__(cfg)
        self.merged_states = []
        self.merged_transitions = {}
        self.merged_action = {}
        self.merged_goto = {}
        self.merge_states()

    def merge_states(self):
        # Group states by their core (items without lookahead)
        core_map = {}
        for i, state in enumerate(self.states):
            core = frozenset((left, production, dot) for (left, production, dot, _) in state)
            if core not in core_map:
                core_map[core] = []
            core_map[core].append(i)

        # Merge states with the same core
        for merged_state_indices in core_map.values():
            merged_state = set()
            for index in merged_state_indices:
                merged_state.update(self.states[index])
            self.merged_states.append(merged_state)

        # Update transitions
        for (state_index, symbol), target_index in self.transitions.items():
            merged_source = self.get_merged_state_index(state_index)
            merged_target = self.get_merged_state_index(target_index)
            self.merged_transitions[(merged_source, symbol)] = merged_target

        # Update action and goto tables
        for (state_index, symbol), action in self.action.items():
            merged_source = self.get_merged_state_index(state_index)
            self.merged_action[(merged_source, symbol)] = action

        for (state_index, symbol), target_index in self.goto.items():
            merged_source = self.get_merged_state_index(state_index)
            merged_target = self.get_merged_state_index(target_index)
            self.merged_goto[(merged_source, symbol)] = merged_target

    def get_merged_state_index(self, state_index):
        for i, merged_state in enumerate(self.merged_states):
            if self.states[state_index].issubset(merged_state):
                return i
        return None

    def parse(self, string):
        stack = [0]
        input_string = list(string) + ['$']
        index = 0
        while True:
            state = stack[-1]
            symbol = input_string[index]
            action = self.merged_action.get((state, symbol))
            if action is None:
                logging.error(f'Error: No action for state {state}, symbol {symbol}')
                return None
            op, val = action
            if op == 's':
                stack.append(val)
                index += 1
                logging.debug(f'Shift to {val}')
            elif op == 'r':
                left, production = val
                for _ in production:
                    stack.pop()
                state = stack[-1]
                goto_state = self.merged_goto.get((state, left))
                if goto_state is None:
                    logging.error(f'Error: No goto for state {state}, symbol {left}')
                    return None
                stack.append(goto_state)
                logging.debug(f'Reduce by {left} -> {" ".join(production)}')
            elif op == 'acc':
                logging.info('Accepted')
                return True

    def print_tables(self):
        logging.info('Merged States:')
        for i, state in enumerate(self.merged_states):
            str_state = ''
            for item in state:
                str_state += f'[{item[0]}->{" ".join(item[1][:item[2]])}.{" ".join(item[1][item[2]:])}, {item[3]}], '
            logging.info(f'{i}: {str_state}')
        logging.info('Merged Transitions:')
        for (i, symbol), s in self.merged_transitions.items():
            logging.info(f'{i} --{symbol}--> {s}')
        logging.info('Merged Action:')
        for (i, symbol), (op, val) in self.merged_action.items():
            logging.info(f'{i}, {symbol}: {op} {val}')
        logging.info('Merged Goto:')
        for (i, symbol), s in self.merged_goto.items():
            logging.info(f'{i}, {symbol}: {s}')