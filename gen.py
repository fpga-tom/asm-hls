import collections


def get_node_ast(node, node_type):
    '''
    Returns all nodes from AST of type node_type
    :param node: node from which to begin
    :param node_type: type of node to search for
    :return: all nodes of type node_type
    '''
    head, *tail = node

    if head == node_type:
        yield node
    elif isinstance(head, collections.Iterable) and not isinstance(head, str):
        for g in get_node_ast(head, node_type):
            yield g

    for child in tail:
        if isinstance(child, collections.Iterable) and not isinstance(child, str):
            for g in get_node_ast(child, node_type):
                yield g


def get_node_cfg(cfg):
    '''
    Traverses control flow graph
    :param cfg: control flow graph
    :return: ordered nodes of control flow graph
    '''
    head, *tail = sorted(cfg.keys(), key=lambda x: x[-1])
    queue = [head]
    visited = set()
    prev = None

    while queue:
        curr = queue.pop(0)
        # if curr not in visited or curr[-1] > prev[-1]:
        yield curr
        nxt = cfg[curr]
        for n in nxt:
            queue.insert(0, n)
        visited.add(curr)
        prev = curr
