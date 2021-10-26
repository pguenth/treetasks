import copy
from src.importancestring import *

# keys: 1 3 5 7 9 8 6 4 2 0 
#       i c h b i m s d e r
# in order of prio: 
#               i
#                 m
#             b
#                   s
#           h
#                     d
#         c
#                       e
#       i
#                         r
a = ImportanceString.from_two_lists("ichbimsder", [1, 3, 5, 7, 9, 8, 6, 4, 2, 0])

# keys: 1 6 5 7 9 8 6 4 6 0 
#       i c h b i m s d e r
# in order of prio: 
#               i
#                 m
#             b
#         c         s   e
#           h
#                     d
#       i
#                         r
b = ImportanceString.from_two_lists("ichbimsder", [1, 6, 5, 7, 9, 8, 6, 4, 6, 0])

def p(a):
    print(a[:5])
    print(a[:-2])
    print(a[3:])
    print(a[7])
    print(a[3:6])

p(b)

def str_to_istr(string):
    return ImportanceString.from_two_lists(string, [0] * len(string))

def prio_path(path_parts):
    ipath_parts = [str_to_istr(s) for s in path_parts]
    slashes = [ImportanceString.from_two_lists("/", [0]) for _ in range(len(path_parts))]

    next_idx = [0] * len(ipath_parts)
    next_importance = sum([len(ip) for ip in ipath_parts]) + len(ipath_parts) - 1
    while len([i for i in next_idx if not i is None]):
        for i, (idx, ipath) in enumerate(zip(next_idx, reversed(ipath_parts))):
            if idx is None:
                continue

            if idx >= len(ipath):
                next_idx[i] = None
            else:
                ipath[idx].importance = next_importance
                next_importance -= 1
                next_idx[i] += 1

            if idx == 0:
                slashes[i][0].importance = next_importance
                next_importance -= 1

    concat = ipath_parts.pop(0)
    for ip, s in zip(ipath_parts, reversed(slashes[:-1])):
        concat += s
        concat += ip

    print(repr(concat))

    return concat
path = ["ich", "bims", "der", "haug"]
pp = prio_path(path)

for i in range(len(pp)):
    print(pp[:i])

def path_cut_ratio(path_parts, lim):
    path_parts = copy.copy(path_parts)
    count = len(path_parts)
    max_len = sum([len(p) for p in path_parts]) + count - 1
    if lim <= count * 2 - 1:
        rstr = ""
        for i, part in enumerate(reversed(path_parts)):
            if i == 0:
                if lim - len(rstr) < 1:
                    break
                rstr = part[0] + rstr
            else:
                if lim - len(rstr) < 2:
                    break
                rstr = part[0] + "/" + rstr

        return rstr 

    elif lim < max_len:
        print("test")
        cut_diff = max_len - lim
        cut_ratio = cut_diff / max_len
        print(cut_diff, cut_ratio)
        for i, part in enumerate(path_parts):
            remove = int(cut_ratio * len(part)) + 1
            print("rp", remove, part)
            path_parts[i] = part[:-remove]
            print("pp", path_parts[i])
            cut_diff -= remove
            if cut_diff <= 0:
                break

        index = 0
        while cut_diff > 0:
            path_parts[index] = path_parts[index][:-1]
            cut_diff -= 1
            index += 1
            if index > count:
                index -= count

    return "/".join(path_parts)

# ranger style
def path_cut(path_parts, lim):
    path_parts = copy.copy(path_parts)
    count = len(path_parts)
    max_len = sum([len(p) for p in path_parts]) + count - 1
    slash_count = count - 1
    if lim <= count + slash_count:
        rstr = ""
        for i, part in enumerate(reversed(path_parts)):
            if i == 0:
                if lim - len(rstr) < 1:
                    break
                rstr = part[0] + rstr
            else:
                if lim - len(rstr) < 2:
                    break
                rstr = part[0] + "/" + rstr

        return rstr 
    elif lim < max_len:
        part_lengths = [1] * count
        filling_index = count - 1
        while sum(part_lengths) < lim - slash_count:
            if part_lengths[filling_index] == len(path_parts[filling_index]):
                if filling_index == count - 1 and filling_index != 0:
                    filling_index = 0
                elif filling_index == 0 and count > 2:
                    filling_index = count - 2
                else:
                    filling_index -= 1
                if filling_index < 0:
                    break
            part_lengths[filling_index] += 1

        path_parts = [p[:l] for p, l in zip(path_parts, part_lengths)]

    return "/".join(path_parts)
            
            
maxpath = len("/".join(path))
for i in range(maxpath + 10):
    newstr = path_cut(path, i)
    print(i, len(newstr), path_cut(path, i))






