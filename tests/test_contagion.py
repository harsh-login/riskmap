import pytest
from collections import deque

def test_bfs_depth_cap():
    # Simple linear graph A-B-C-D-E
    adjacency_list = {
        1: [(2, 1.0)],
        2: [(1, 1.0), (3, 1.0)],
        3: [(2, 1.0), (4, 1.0)],
        4: [(3, 1.0), (5, 1.0)],
        5: [(4, 1.0)]
    }
    
    source = 1
    max_depth = 3
    
    visited = {source: 0}
    queue = deque([(source, 0)])
    
    affected = []
    
    while queue:
        current, depth = queue.popleft()
        if depth > 0:
            affected.append((current, depth))
            
        if depth < max_depth:
            for neighbor, _ in adjacency_list.get(current, []):
                if neighbor not in visited:
                    visited[neighbor] = depth + 1
                    queue.append((neighbor, depth + 1))
                    
    # Should only reach nodes up to depth 3: 2, 3, 4. Node 5 is at depth 4.
    affected_nodes = [n for n, d in affected]
    assert 2 in affected_nodes
    assert 3 in affected_nodes
    assert 4 in affected_nodes
    assert 5 not in affected_nodes
