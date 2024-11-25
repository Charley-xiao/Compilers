def is_non_terminal(symbol):
    return symbol.isupper() or symbol == "S'"

def is_terminal(symbol):
    return not is_non_terminal(symbol)