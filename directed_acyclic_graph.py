
import matplotlib.pyplot as plt


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


lst = [
    (0.0, 2.0), (0.0, 4.0), (2.5, 4.5), (2.0, 5.75),
    (2.0, 4.0), (6.0, 7.25), (4.0, 5.5)
]

sept_haikai = [(0.0, 4.0), (2.5, 4.75), (4.0, 5.25), (5.75, 9.75), (8.25, 11.25), (9.75, 12.25), (10.25, 13.25), (13.25, 14.5), (15.0, 19.0), (19.0, 19.875), (19.375, 20.875), (20.875, 22.125), (21.625, 23.125), (23.125, 27.625), (26.125, 29.625), (27.625, 30.625), (30.625, 31.5), (31.0, 32.5), (31.5, 34.0), (34.0, 35.0), (34.625, 35.875), (35.875, 37.125), (36.375, 37.625), (38.125, 39.0), (38.5, 40.0), (40.0, 41.25), (41.75, 45.75), (45.75, 46.625), (46.125, 47.625), (47.625, 48.875), (49.375, 53.375), (51.875, 54.875), (53.375, 55.875), (53.875, 56.875), (56.875, 58.125), (58.625, 62.625), (61.125, 63.375), (62.625, 63.875), (64.5, 66.0), (4.0, 5.75), (13.25, 15.0), (19.0, 20.875), (20.875, 22.625), (24.625, 29.625), (26.125, 30.625), (30.625, 32.5), (31.0, 33.5), (32.5, 34.625), (34.625, 36.375), (35.375, 37.125), (36.375, 38.125), (38.125, 40.0), (40.0, 41.75), (45.75, 47.625), (47.625, 49.375), (56.875, 58.625), (62.625, 64.375), (8.25, 13.25), (51.875, 56.875), (5.75, 13.25), (22.625, 30.625), (49.375, 56.875)]

print(get_all_end_overlap_tups(sept_haikai))

import networkx as nx

G = nx.DiGraph()
#G.add_edges_from([('16', '17'), ('3', '41'), ('41', '39'), ('42', '39')])

G.add_edges_from(sept_haikai)
roots = []
leaves = []
for node in G.nodes :
  if G.in_degree(node) == 0 : # it's a root
    roots.append(node)
  elif G.out_degree(node) == 0 : # it's a leaf
    leaves.append(node)

all_paths = []
for root in roots :
  for leaf in leaves :
    for path in nx.all_simple_paths(G, root, leaf):
      all_paths.append(path)

for this_path in all_paths:
    if this_path[0] == 0.0 and this_path[-1] == 64.375:
        print(this_path)

#nx.draw_networkx(G, pos=nx.circular_layout(G))
#plt.show()

