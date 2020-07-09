def overlap_condition(tup1, tup2):
    if tup1 == tup2:
        return False
    a, b = tup1
    c, d = tup2
    return b <= c


def adj_mat_from_tup_list(tup_lst):
    return [
        [
            1 if overlap_condition(tup_lst[i], tup_lst[j]) else 0
            for j in range(len(tup_lst))
        ] for i in range(len(tup_lst))

    ]


def topological_sort(adj_mat):
    sorted_v = []
    sinks = {
        i for i in range(len(adj_mat))
        if not any(adj_mat[j][i] == 1 for j in range(len(adj_mat)))
    }

    while sinks:
        v = sinks.pop()
        sorted_v += [v]
        for j in range(len(adj_mat)):
            if adj_mat[v][j] == 1:
                adj_mat[v][j] = 0
                if not any(adj_mat[w][j] for w in range(len(adj_mat))):
                    sinks.add(j)
    return sorted_v


def get_longest_path(adj_mat, sorted_v):
    dists = {v: 0 for v in range(len(adj_mat))}
    preds = {v: None for v in range(len(adj_mat))}
    for v in sorted_v:
        for u in range(len(adj_mat)):
            if adj_mat[u][v]:
                dists[v] = max(dists[v], dists[u] + 1)
                preds[v] = u

    current_v = {
        v for v in range(len(adj_mat))
        if dists[v] == max(dists.values())
    }.pop()
    result = [current_v]
    while preds[current_v] is not None:
        current_v = preds[current_v]
        result += [current_v]
    return result[::-1]


def get_all_end_overlap_tups(tup_lst):
    sorted_v = topological_sort(adj_mat_from_tup_list(tup_lst))
    adj_mat = adj_mat_from_tup_list(tup_lst)
    return [tup_lst[i] for i in get_longest_path(adj_mat, sorted_v)]

#to pick best, use formula to decide which has "better" talas

'''
tup_lst = [
    (0.0, 2.0), (0.0, 4.0), (2.5, 4.5), (2.0, 5.75),
    (2.0, 4.0), (6.0, 7.25), (4.0, 5.5)
]
'''

'''
one thing that would make this faster is to first search through and find any ranges that are non overlapping with *all* of the rest
this could significantly shorten this process.
'''

def get_all_longest_paths(tup_lst):
    sources = {
        (a, b)
        for (a, b) in tup_lst
        if not any(d <= a for (c, d) in tup_lst)
    } 

    sinks = {
        (a, b)
        for (a, b) in tup_lst
        if not any(b <= c for (c, d) in tup_lst)
    }

    min_successor = {
        (a, b): min(d for c, d in tup_lst if c >= b)
        for (a, b) in set(tup_lst) - sinks
    }

    successors = {
        (a, b): [
            (c, d)
            for (c, d) in tup_lst
            if b <= c <= d and c < min_successor[(a, b)]
        ] for (a, b) in tup_lst
    }

    solutions = []
    def print_path_rec(node, path):
        if node in sinks:
            solutions.append([path + [node]])
            print(len(solutions))
            if len(solutions) == 100:
                print('just passed...')
        else:
            for successor in successors[node]:
                print_path_rec(successor, path + [node])

    for source in sources:
        print_path_rec(source, [])

    flatten = lambda l: [item for sublist in l for item in sublist]
    flattened = flatten(solutions)

    return flattened

#full = [(0.0, 4.0), (2.5, 4.75), (4.0, 5.25), (5.75, 9.75), (8.25, 11.25), (9.75, 12.25), (10.25, 13.25), (13.25, 14.5), (15.0, 19.0), (19.0, 19.875), (19.375, 20.875), (20.875, 22.125), (21.625, 23.125), (23.125, 27.625), (26.125, 29.625), (27.625, 30.625), (30.625, 31.5), (31.0, 32.5), (31.5, 34.0), (34.0, 35.0), (34.625, 35.875), (35.875, 37.125), (36.375, 37.625), (38.125, 39.0), (38.5, 40.0), (40.0, 41.25), (41.75, 45.75), (45.75, 46.625), (46.125, 47.625), (47.625, 48.875), (49.375, 53.375), (51.875, 54.875), (53.375, 55.875), (53.875, 56.875), (56.875, 58.125), (58.625, 62.625), (61.125, 63.375), (62.625, 63.875), (64.5, 66.0), (4.0, 5.75), (13.25, 15.0), (19.0, 20.875), (20.875, 22.625), (24.625, 29.625), (26.125, 30.625), (30.625, 32.5), (31.0, 33.5), (32.5, 34.625), (34.625, 36.375), (35.375, 37.125), (36.375, 38.125), (38.125, 40.0), (40.0, 41.75), (45.75, 47.625), (47.625, 49.375), (56.875, 58.625), (62.625, 64.375), (8.25, 13.25), (51.875, 56.875), (5.75, 13.25), (22.625, 30.625), (49.375, 56.875)]
#sorted_full = sorted(full, key = lambda x: x[0])
'''
new_sept_haikai_data = [(0.0, 4.0), (2.5, 4.75), (4.0, 5.25), (4.0, 5.75), (5.75, 9.75), (5.75, 13.25), (8.25, 11.25), (8.25, 13.25), (9.75, 12.25), (10.25, 13.25), (13.25, 14.5), (13.25, 15.0), (15.0, 19.0), (19.0, 19.875), (19.0, 20.875), (19.375, 20.875), (20.875, 22.125), (20.875, 22.625), (21.625, 23.125), (22.625, 30.625), (23.125, 27.625), (24.625, 29.625), (26.125, 29.625), (26.125, 30.625), (27.625, 30.625), (30.625, 31.5), (30.625, 32.5), (31.0, 32.5), (31.0, 33.5), (31.5, 34.0), (32.5, 34.625), (34.0, 35.0), (34.625, 35.875), (34.625, 36.375), (35.375, 37.125), (35.875, 37.125), (36.375, 37.625), (36.375, 38.125), (38.125, 39.0), (38.125, 40.0), (38.5, 40.0), (40.0, 41.25), (40.0, 41.75), (41.75, 45.75), (45.75, 46.625), (45.75, 47.625), (46.125, 47.625), (47.625, 48.875), (47.625, 49.375), (49.375, 53.375), (49.375, 56.875), (51.875, 54.875), (51.875, 56.875), (53.375, 55.875), (53.875, 56.875), (56.875, 58.125), (56.875, 58.625), (58.625, 62.625), (61.125, 63.375), (62.625, 63.875), (62.625, 64.375), (64.5, 66.0)]
'''

tup_lst_1 = [(0.0, 4.0), (2.5, 4.75), (4.0, 5.25), (4.0, 5.75), (5.75, 9.75), (5.75, 13.25), (8.25, 11.25), (8.25, 13.25), (9.75, 12.25), (10.25, 13.25), (13.25, 14.5), (13.25, 15.0)]
tup_lst_2 = [(15.0, 19.0), (19.0, 19.875), (19.0, 20.875), (19.375, 20.875), (20.875, 22.125), (20.875, 22.625), (21.625, 23.125), (22.625, 30.625), (23.125, 27.625), (24.625, 29.625), (26.125, 29.625), (26.125, 30.625), (27.625, 30.625), (30.625, 31.5), (30.625, 32.5), (31.0, 32.5), (31.0, 33.5), (31.5, 34.0), (32.5, 34.625), (34.0, 35.0), (34.625, 35.875), (34.625, 36.375), (35.375, 37.125), (35.875, 37.125), (36.375, 37.625), (36.375, 38.125)]
tup_lst3 = [(38.125, 39.0), (38.125, 40.0), (38.5, 40.0), (40.0, 41.25), (40.0, 41.75), (41.75, 45.75), (45.75, 46.625), (45.75, 47.625), (46.125, 47.625)]
tup_lst4 = [(47.625, 48.875), (47.625, 49.375), (49.375, 53.375), (49.375, 56.875), (51.875, 54.875), (51.875, 56.875), (53.375, 55.875), (53.875, 56.875), (56.875, 58.125), (56.875, 58.625), (58.625, 62.625), (61.125, 63.375), (62.625, 63.875), (62.625, 64.375), (64.5, 66.0)]

partitions = [tup_lst_1, tup_lst_2, tup_lst3, tup_lst4]

for i, this_partition in enumerate(partitions):
    print('*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-')
    print('PARTITION {}'.format(str(i)))
    for x in get_all_longest_paths(this_partition):
        print(x)
    print('*-*-*-*-*-*-*-*-*-*-*-*')

'''
for x in sorted_full:
    print(x[0])
'''

#tup_lst1 = [(0.0, 4.0), (2.5, 4.75), (4.0, 5.25), (5.75, 9.75), (8.25, 11.25), (9.75, 12.25), (10.25, 13.25), (13.25, 14.5), (15.0, 19.0)]
#tup_lst2 = [(19.0, 19.875), (19.375, 20.875), (20.875, 22.125), (21.625, 23.125), (23.125, 27.625), (26.125, 29.625), (27.625, 30.625), (30.625, 31.5), (31.0, 32.5), (31.5, 34.0)]
#tup_lst3 = [(34.0, 35.0), (34.625, 35.875), (35.875, 37.125), (36.375, 37.625), (38.125, 39.0), (38.5, 40.0), (40.0, 41.25), (41.75, 45.75), (45.75, 46.625), (46.125, 47.625)]
#tup_lst4 = [(47.625, 48.875), (49.375, 53.375), (51.875, 54.875), (53.375, 55.875), (53.875, 56.875), (56.875, 58.125), (58.625, 62.625), (61.125, 63.375), (62.625, 63.875), (64.5, 66.0)]#, (4.0, 5.75), (13.25, 15.0), (19.0, 20.875), (20.875, 22.625), (24.625, 29.625), (26.125, 30.625), (30.625, 32.5), (31.0, 33.5), (32.5, 34.625), (34.625, 36.375), (35.375, 37.125), (36.375, 38.125), (38.125, 40.0), (40.0, 41.75), (45.75, 47.625), (47.625, 49.375), (56.875, 58.625), (62.625, 64.375), (8.25, 13.25), (51.875, 56.875), (5.75, 13.25), (22.625, 30.625), (49.375, 56.875)]
'''
print('TUP LIST 1')
for x in get_all_longest_paths(sorted_full):
    print(x)
print('*-*-*-*-*-*-*-*-*-*-*-*')

print('TUP LIST 2')
for x in get_all_longest_paths(tup_lst2):
    print(x)
print('*-*-*-*-*-*-*-*-*-*-*-*')
'''
'''
WANT:
[(0.0, 2.0), (2.5, 4.5), (6.0, 7.25)]
[(0.0, 2.0), (2.0, 5.75), (6.0, 7.25)]
[(0.0, 2.0), (2.0, 4.0), (4.0, 5.5), (6.0, 7.25)]
[(0.0, 4.0), (4.0, 5.5), (6.0, 7.25)]
'''

#print(get_all_end_overlap_tups(lst))