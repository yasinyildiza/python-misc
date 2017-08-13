"""
     |
    | |
   |   |
  | | | |
 |   | | |
| | | | |  


     |     
    | |
   | | |
  | | | |
 | | | | |
| | | | | |
"""

class Node:
    def __init__(self, x=None, l=None, r=None):
        self.x = x
        self.l = l
        self.r = r

T1 = Node("root",
    Node("l",
        Node("ll",
            Node("lll",
                Node("llll",
                    None,
                    Node("llllr", None, None)),
                None),
            Node("llr",
                None,
                Node("llrr",
                    Node("llrrl", None, None),
                    Node("llrrr", None, None)))),
        None),
    Node("r",
        None,
        Node("rr",
            Node("rrl",
                Node("rrll",
                    Node("rrlll", None, None),
                    Node("rrllr", None, None)),
                Node("rrlr",
                    Node("rrlrl", None, None),
                    Node("rrlrr", None, None))),
            Node("rrr",
                Node("rrrl",
                    Node("rrrll", None, None),
                    Node("rrrlr", None, None)),
                Node("rrrr",
                    Node("rrrrl", None, None),
                    None)
                )
            )
        )
    )

T2 = None

T3 = Node("root", None, None)

T4 = Node("root",
    Node("l", None, None),
    None)

T5 = Node("root",
    Node("l",
        Node("ll",
            Node("lll",
                Node("llll",
                    Node("lllll", None, None),
                    Node("llllr", None, None)),
                Node("lllr",
                    Node("lllrl", None, None),
                    Node("lllrr", None, None))),
            Node("llr",
                Node("llrl",
                    Node("llrll", None, None),
                    Node("llrlr", None, None)),
                Node("llrr",
                    Node("llrrl", None, None),
                    Node("llrrr", None, None)))),
        Node("lr",
            Node("lrl",
                Node("lrll",
                    Node("lrlll", None, None),
                    Node("lrllr", None, None)),
                Node("lrlr",
                    Node("lrlrl", None, None),
                    Node("lrlrr", None, None))),
            Node("lrr",
                Node("lrrl",
                    Node("lrrll", None, None),
                    Node("lrrlr", None, None)),
                Node("lrrr",
                    Node("lrrrl", None, None),
                    Node("lrrrr", None, None))))),
    Node("r",
        Node("rl",
            Node("rll",
                Node("rlll",
                    Node("rllll", None, None),
                    Node("rlllr", None, None)),
                Node("rllr",
                    Node("rllrl", None, None),
                    Node("rllrr", None, None))),
            Node("rlr",
                Node("rlrl",
                    Node("rlrll", None, None),
                    Node("rlrlr", None, None)),
                Node("rlrr",
                    Node("rlrrl", None, None),
                    Node("rlrrr", None, None)))),
        Node("rr",
            Node("rrl",
                Node("rrll",
                    Node("rrlll", None, None),
                    Node("rrllr", None, None)),
                Node("rrlr",
                    Node("rrlrl", None, None),
                    Node("rrlrr", None, None))),
            Node("rrr",
                Node("rrrl",
                    Node("rrrll", None, None),
                    Node("rrrlr", None, None)),
                Node("rrrr",
                    Node("rrrrl", None, None),
                    Node("rrrrr", None, None))))))

DIRECTION_LEFT  = 0
DIRECTION_RIGHT = 1

def find_zipzag(t, direction):
    if t is None:
        return 0

    check = False

    if direction == DIRECTION_LEFT and t.r is not None:
        check = True

    if direction == DIRECTION_RIGHT and t.l is not None:
        check = True

    l = find_zipzag(t.l, DIRECTION_LEFT)
    r = find_zipzag(t.r, DIRECTION_RIGHT)

    return int(check) + max(l, r)

def find_zigzags(T):
    if T is None:
        return 0

    l = find_zipzag(T.l, DIRECTION_LEFT)
    r = find_zipzag(T.r, DIRECTION_RIGHT)

    return max(l, r)

def find_depth(t, depth):
    if t is None:
        return 0

    l = find_depth(t.l, depth)
    r = find_depth(t.r, depth)

    return depth + max(l, r) + 1

def print_level(matrix, t, level, depth):
    if t is None:
        return

    print_level(matrix, t.l, level+1, depth-1)
    print_level(matrix, t.r, level+1, depth-1)

def solution_depth(T):
    depth = find_depth(T, 0)
    print('depth : {depth}'.format(depth=depth))

def solution_zigzag(T):
    zigzag = find_zigzags(T)
    print('zipzag: {zipzag}'.format(zipzag=zigzag))

def solution(T):
    solution_depth(T)
    solution_zigzag(T)

def main():
    solution(T1)
    solution(T2)
    solution(T3)
    solution(T4)
    solution(T5)

if __name__ == '__main__':
    main()
