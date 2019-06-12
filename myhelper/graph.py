class Graph(object):

    def __init__(self, nodes=list(), edges=list()):
        self.node_neighbors = {}
        self.visited = {}
        self.maps = {}
        if len(nodes):
            self.add_nodes(nodes)
        if len(edges):
            for e in edges:
                self.add_edge(e)

    def add_nodes(self,nodelist):

        for node in nodelist:
            self.add_node(node)

    def add_node(self,node):
        if not node in self.nodes():
            self.node_neighbors[node] = []

    def add_edge(self,edge):
        u,v = edge
        if(v not in self.node_neighbors[u]) and ( u not in self.node_neighbors[v]):
            self.node_neighbors[u].append(v)
            self.maps[(u,v)] = True
            self.maps[(v,u)] = False

            if(u!=v):
                self.node_neighbors[v].append(u)

    def nodes(self):
        return self.node_neighbors.keys()

    def depth_first_search(self,root=None):
        order = []
        def dfs(node):
            self.visited[node] = True
            order.append(node)
            for n in self.node_neighbors[node]:
                if not self.maps[(node,n)]:
                    continue
                if not n in self.visited:
                    dfs(n)


        if root:
            dfs(root)

        # for node in self.nodes():
        #     if not node in self.visited:
        #         dfs(node)

        #print (order)
        self.visited.clear()
        return order

    def depth_first_search_path(self, root=None, end=None):
        order = []
        paths = []

        def dfs_all_paths(start=None, end=None):
            self.visited[start] = True
            order.append(start)
            for n in self.node_neighbors[start]:
                if start == end:
                    paths.append(order.copy())
                    order.pop()
                    self.visited[start] = False
                    break
                if not self.maps[(start,n)]:
                    if n == self.node_neighbors[start][-1]:
                        order.pop()
                        self.visited[start] = False
                    continue
                if not n in self.visited or self.visited[n] == False:
                    dfs_all_paths(n, end)
                if n == self.node_neighbors[start][-1]:
                    order.pop()
                    self.visited[start] = False


        if root:
            dfs_all_paths(root, end)

        self.visited.clear()
        if not paths:
            paths.append([]);

        return paths

    def breadth_first_search(self,root=None):
        queue = []
        order = []
        def bfs():
            while len(queue)> 0:
                node  = queue.pop(0)

                self.visited[node] = True
                for n in self.node_neighbors[node]:
                    if self.maps[(node, n)]:
                        if (not n in self.visited) and (not n in queue):
                            queue.append(n)
                            order.append(n)

        if root:
            queue.append(root)
            order.append(root)
            bfs()

        # for node in self.nodes():
        #     if not node in self.visited:
        #         queue.append(node)
        #         order.append(node)
        #         bfs()
        #print (order)

        self.visited.clear()
        return order