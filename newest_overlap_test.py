from itertools import *
import operator
from functools import reduce
import tqdm

def allsubsets(l):
    for s in chain(*map(lambda r: combinations(l,r), range(1,len(l))) ):
        yield s

def mk_cover(acc, item):
    ((curlo, curhi), tuplist, ovl) = acc
    (newlo, newhi) = item
    if newlo<=curhi:
        if newhi>=curhi:
            overlap = curhi - newlo
        else:
            overlap = newhi - newlo
            newhi   = curhi
        return ((curlo, newhi), tuplist+[item], ovl+overlap)
    else:
        return acc

def mk_finder(lo, hi):
    def overlapper(acc, tuples):
        tuples = list(sorted(tuples, key=operator.itemgetter(0)))
        ((covlo, covhi), tl, ovl) = reduce(mk_cover, tuples[1:], (tuples[0], [tuples[0]], 0))
        if covlo<=lo and covhi>=hi:
            acc.append(((covlo, covhi), tl, ovl))
        return acc
    return overlapper


inp = [(0, 5), (0, 10), (5, 8), (5, 10), (8, 10), (10,20), (20,30), (22,24), (26,30), (10,28), (25, 30), (30, 40)]
#print(inp)

indices = [(0.0, 2.0), (0.0, 4.0), (2.5, 4.5), (2.0, 5.75), (2.0, 4.0), (6.0, 7.25), (4.0, 5.5)]
sept_haikai = [(0.0, 4.0), (2.5, 4.75), (4.0, 5.25), (5.75, 9.75), (8.25, 11.25), (9.75, 12.25), (10.25, 13.25), (13.25, 14.5), (15.0, 19.0), (19.0, 19.875), (19.375, 20.875), (20.875, 22.125), (21.625, 23.125), (23.125, 27.625), (26.125, 29.625), (27.625, 30.625), (30.625, 31.5), (31.0, 32.5), (31.5, 34.0), (34.0, 35.0), (34.625, 35.875), (35.875, 37.125), (36.375, 37.625), (38.125, 39.0), (38.5, 40.0), (40.0, 41.25), (41.75, 45.75), (45.75, 46.625), (46.125, 47.625), (47.625, 48.875), (49.375, 53.375), (51.875, 54.875), (53.375, 55.875), (53.875, 56.875), (56.875, 58.125), (58.625, 62.625), (61.125, 63.375), (62.625, 63.875), (64.5, 66.0), (4.0, 5.75), (13.25, 15.0), (19.0, 20.875), (20.875, 22.625), (24.625, 29.625), (26.125, 30.625), (30.625, 32.5), (31.0, 33.5), (32.5, 34.625), (34.625, 36.375), (35.375, 37.125), (36.375, 38.125), (38.125, 40.0), (40.0, 41.75), (45.75, 47.625), (47.625, 49.375), (56.875, 58.625), (62.625, 64.375), (8.25, 13.25), (51.875, 56.875), (5.75, 13.25), (22.625, 30.625), (49.375, 56.875)]

# find all that cover 10,30
found = reduce(mk_finder(10, 30), allsubsets(inp), [])

#sort by overlap
new = [(tl, ovl) for (cov, tl, ovl) in sorted(found, key=operator.itemgetter(2))]
for x in tqdm.tqdm(new):
    if x[1] == 0:
        print(x)

#for x in allsubsets(l = indices):
    #print(x)