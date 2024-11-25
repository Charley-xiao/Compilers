import tkinter as tk
from tkinter import ttk, messagebox
from functools import partial

class ParserUI:
    def __init__(self, root, parsers, default_cfg):
        self.root = root
        self.parsers = parsers 
        self.default_cfg = default_cfg
        self.current_parser = None 
        self.parser_class = None 

        root.title("Parser UI: SLR, CLR, LALR")
        root.geometry("900x700")
        root.resizable(False, False)
        ttk.Label(root, text="Parser UI", font=("Helvetica", 18)).pack(pady=10)
        parser_frame = ttk.Frame(root)
        parser_frame.pack(pady=10)
        ttk.Label(parser_frame, text="Select Parser:").grid(row=0, column=0, padx=5, pady=5)
        self.parser_selection = ttk.Combobox(parser_frame, values=list(self.parsers.keys()), state="readonly")
        self.parser_selection.grid(row=0, column=1, padx=5, pady=5)
        self.parser_selection.current(0)
        self.parser_selection.bind("<<ComboboxSelected>>", self.on_parser_change)

        self.grammar_frame = ttk.Labelframe(root, text="Grammar")
        self.grammar_frame.pack(padx=10, pady=10, fill="x")
        self.grammar_text = tk.Text(self.grammar_frame, height=8)
        self.grammar_text.pack(padx=10, pady=5, fill="both", expand=True)
        self.grammar_text.insert("1.0", self.format_cfg(self.default_cfg))

        self.input_frame = ttk.Frame(root)
        self.input_frame.pack(padx=10, pady=10, fill="x")
        ttk.Label(self.input_frame, text="Input String:").grid(row=0, column=0, padx=5, pady=5)
        self.input_entry = ttk.Entry(self.input_frame, width=50)
        self.input_entry.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(self.input_frame, text="Parse", command=self.run_parser).grid(row=0, column=2, padx=5, pady=5)

        self.output_tabs = ttk.Notebook(root)
        self.output_tabs.pack(padx=10, pady=10, fill="both", expand=True)

        self.steps_tab = ttk.Frame(self.output_tabs)
        self.action_table_tab = ttk.Frame(self.output_tabs)
        self.goto_table_tab = ttk.Frame(self.output_tabs)
        self.output_tabs.add(self.steps_tab, text="Parsing Steps")
        self.output_tabs.add(self.action_table_tab, text="Action Table")
        self.output_tabs.add(self.goto_table_tab, text="Goto Table")

        self.steps_text = tk.Text(self.steps_tab, state="disabled")
        self.steps_text.pack(padx=10, pady=10, fill="both", expand=True)

        self.action_tree = ttk.Treeview(self.action_table_tab, columns=("State", "Symbol", "Action"), show="headings")
        self.action_tree.heading("State", text="State")
        self.action_tree.heading("Symbol", text="Symbol")
        self.action_tree.heading("Action", text="Action")
        self.action_tree.pack(padx=10, pady=10, fill="both", expand=True)

        self.goto_tree = ttk.Treeview(self.goto_table_tab, columns=("State", "Symbol", "Goto"), show="headings")
        self.goto_tree.heading("State", text="State")
        self.goto_tree.heading("Symbol", text="Symbol")
        self.goto_tree.heading("Goto", text="Goto")
        self.goto_tree.pack(padx=10, pady=10, fill="both", expand=True)

        self.on_parser_change()

    def format_cfg(self, cfg):
        formatted = ""
        for head, productions in cfg.items():
            formatted += f"{head} -> {' | '.join(' '.join(prod) for prod in productions)}\n"
        return formatted

    def on_parser_change(self, event=None):
        parser_name = self.parser_selection.get()
        self.parser_class = self.parsers[parser_name]
        messagebox.showinfo("Parser Changed", f"Switched to {parser_name} Parser")

    def run_parser(self):
        try:
            input_string = self.input_entry.get().strip()
            if not input_string:
                messagebox.showerror("Error", "Input string cannot be empty.")
                return

            grammar_text = self.grammar_text.get("1.0", "end").strip()
            cfg = self.parse_cfg(grammar_text)

            self.current_parser = self.parser_class(cfg)

            self.clear_output()

            self.fill_action_table()
            self.fill_goto_table()
            self.run_and_display_steps(input_string)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def parse_cfg(self, grammar_text):
        cfg = {}
        for line in grammar_text.splitlines():
            line = line.strip()
            if not line or "->" not in line:
                continue
            head, productions = line.split("->", 1)
            head = head.strip()
            production_list = [tuple(prod.strip().split()) for prod in productions.split("|")]
            cfg[head] = production_list
        return cfg

    def clear_output(self):
        self.steps_text.config(state="normal")
        self.steps_text.delete("1.0", "end")
        self.steps_text.config(state="disabled")

        for tree in [self.action_tree, self.goto_tree]:
            for item in tree.get_children():
                tree.delete(item)

    def fill_action_table(self):
        for (state, symbol), (op, val) in self.current_parser.action.items():
            self.action_tree.insert("", "end", values=(state, symbol, f"{op} {val}"))

    def fill_goto_table(self):
        for (state, symbol), target in self.current_parser.goto.items():
            self.goto_tree.insert("", "end", values=(state, symbol, target))

    def run_and_display_steps(self, input_string):
        def log_step(message):
            self.steps_text.config(state="normal")
            self.steps_text.insert("end", message + "\n")
            self.steps_text.config(state="disabled")

        log_step("Parsing Input: " + input_string)
        stack = [0]
        input_string += "$"
        index = 0

        while True:
            state = stack[-1]
            symbol = input_string[index]
            action = self.current_parser.action.get((state, symbol))
            if action is None:
                log_step(f"Error: No action for state {state}, symbol {symbol}")
                return
            op, val = action
            if op == "s":
                stack.append(val)
                index += 1
                log_step(f"Shift to state {val}")
            elif op == "r":
                left, production = val
                for _ in production:
                    stack.pop()
                state = stack[-1]
                goto_state = self.current_parser.goto.get((state, left))
                if goto_state is None:
                    log_step(f"Error: No goto for state {state}, symbol {left}")
                    return
                stack.append(goto_state)
                log_step(f"Reduce by {left} -> {' '.join(production)}")
            elif op == "acc":
                log_step("Accepted")
                return


if __name__ == "__main__":
    from parsers import SLRParser, CLRParser, LALRParser

    parsers = {
        "SLR": SLRParser,
        "CLR": CLRParser,
        "LALR": LALRParser
    }

    cfg = {
        "S'": [('S',)],
        'S': [('S', 'A'), ('S', 'B'), ('a',)],
        'A': [('S', '+')],
        'B': [('S', '-')]
    }

    root = tk.Tk()
    app = ParserUI(root, parsers, cfg)
    root.mainloop()
