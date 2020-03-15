import pool

def print_scc(scc):
    for n in sorted((n for n in scc if isinstance(n, pool.Reaction)), 
        reverse=True):
        print(n)

