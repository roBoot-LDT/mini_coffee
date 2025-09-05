from collections import deque
from pathlib import Path

class Pathfinder:
    def __init__(self, connections):
        self.graph = self._build_graph(connections)

    def _build_graph(self, connections):
        graph = {}
        for connection in connections:
            src, dest = connection
            if src not in graph:
                graph[src] = []
            if dest not in graph:
                graph[dest] = []
            graph[src].append(dest)
            graph[dest].append(src)
        return graph

    def find_path(self, start, end):
        if start not in self.graph or end not in self.graph:
            return None

        visited = set()
        queue = deque([[start]])

        while queue:
            path = queue.popleft()
            node = path[-1]

            if node == end:
                return path

            if node not in visited:
                visited.add(node)
                for neighbor in self.graph.get(node, []):
                    new_path = list(path)
                    new_path.append(neighbor)
                    queue.append(new_path)

        return None
    
def get_env_path() -> Path:
    """
    Searches for a '.env' file in the current or parent directories.

    Raises:
        FileNotFoundError: If no '.env' file is found in any parent directory.

    Returns:
        pathlib.Path: The path to the found '.env' file.
    """
    current = Path(__file__).resolve().parent

    for parent in current.parents:
        candidate = parent / ".env"
        if candidate.exists():
            return candidate
    raise FileNotFoundError(".env file not found in any parent directory")

if __name__ == "__main__":
    get_env_path()