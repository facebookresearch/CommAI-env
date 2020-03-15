import term

def all_reductions(t):
    for tr,_,_ in term.all_reductions(t):
        yield tr

def print_all(ts):
    for t in ts:
        print(term.to_str(t))
