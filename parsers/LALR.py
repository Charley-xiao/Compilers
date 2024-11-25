import logging 
from .symbols import is_terminal, is_non_terminal
from .CLR import CLRParser

class LALRParser(CLRParser):
    def __init__(self, cfg):
        self.states_raw = []  # To keep raw states before merging
        super().__init__(cfg)
        self.merge_states()

    def merge_states(self):
        # Group states by their core (items without lookahead)
        core_map = {}
        for i, state in enumerate(self.states):
            core = frozenset((left, production, dot) for (left, production, dot, _) in state)
            if core not in core_map:
                core_map[core] = []
            core_map[core].append(i)

        # Mapping from old state indices to new merged state indices
        state_mapping = {}
        new_states = []
        for indices in core_map.values():
            # Merge lookaheads for identical items
            merged_items = {}
            for index in indices:
                for item in self.states[index]:
                    key = (item[0], item[1], item[2])
                    if key not in merged_items:
                        merged_items[key] = set()
                    merged_items[key].add(item[3])
            # Convert back to set of items
            new_state = set()
            for key, lookaheads in merged_items.items():
                for lookahead in lookaheads:
                    new_state.add((*key, lookahead))
            new_state_index = len(new_states)
            for index in indices:
                state_mapping[index] = new_state_index
            new_states.append(new_state)
        self.states = new_states

        # Update transitions
        new_transitions = {}
        for (state_index, symbol), target_index in self.transitions.items():
            merged_source = state_mapping[state_index]
            merged_target = state_mapping[target_index]
            new_transitions[(merged_source, symbol)] = merged_target
        self.transitions = new_transitions

        # Rebuild action and goto tables based on merged states
        self.action = {}
        self.goto = {}
        for i, state in enumerate(self.states):
            for (left, production, dot, lookahead) in state:
                if dot < len(production):
                    symbol = production[dot]
                    if is_terminal(symbol):
                        s = self.transitions.get((i, symbol))
                        if s is not None:
                            key = (i, symbol)
                            # Handle shift conflicts
                            if key in self.action and self.action[key] != ('s', s):
                                raise ValueError(f'Conflict at state {i}, symbol {symbol}')
                            self.action[key] = ('s', s)
                    else:
                        s = self.transitions.get((i, symbol))
                        if s is not None:
                            self.goto[(i, symbol)] = s
                else:
                    if left == "S'":
                        self.action[(i, '$')] = ('acc', None)
                    else:
                        key = (i, lookahead)
                        # Handle reduce conflicts
                        if key in self.action and self.action[key] != ('r', (left, production)):
                            raise ValueError(f'Conflict at state {i}, symbol {lookahead}')
                        self.action[key] = ('r', (left, production))

    def build_states(self):
        logging.info('=========== Building states... ===========')
        start_item = ("S'", self.cfg["S'"][0], 0, '$')
        start_closure = self.build_closure({start_item})
        self.states = [start_closure]
        logging.info(f'State 0: {start_closure}')
        states_added = True
        while states_added:
            states_added = False
            for i, state in enumerate(self.states):
                symbols = set()
                for (left, production, dot, lookahead) in state:
                    if dot < len(production):
                        symbols.add(production[dot])
                for symbol in symbols:
                    goto_state = self.build_goto(state, symbol)
                    # Check if this goto_state is already in self.states
                    if goto_state in self.states:
                        s = self.states.index(goto_state)
                    else:
                        s = len(self.states)
                        self.states.append(goto_state)
                        states_added = True
                    self.transitions[(i, symbol)] = s

    def parse(self, string):
        return super().parse(string)