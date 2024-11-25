import logging
from parsers import SLRParser, CLRParser, LALRParser

def setup_logger():
    logging.basicConfig(level=logging.DEBUG, format='%(message)s')

# Augmented grammar with productions stored as tuples of symbols
cfg = {
    "S'": [('S',)],  # Augmented start symbol
    'S': [('S', 'A'), ('S', 'B'), ('a',)],
    'A': [('S', '+')],
    'B': [('S', '-')]
}

if __name__ == '__main__':
    setup_logger()
    parser = SLRParser(cfg)
    parser.print_tables()
    parser.parse('aaaa+++')
    parser = CLRParser(cfg)
    parser.print_tables()
    parser.parse('aaaa---')
    parser = LALRParser(cfg)
    parser.print_tables()
    parser.parse('aaaa+-+')