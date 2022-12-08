import logging


class TreeNode:

    def __init__(self, address, parent):
        self.children = []
        self.address = address
        self.parent = parent


    def add_child(self, address):
        for child in self.children:
            if address == child.address:
                # node already in tree structure
                return
        logging.debug(f"New child '{address}' added to {self.address}")
        self.children.append(TreeNode(address, self))

    def can_hold_children(self) -> bool:
        child_count = len(self.children)
        if child_count >= 2:
            return False
        else:
            return True

    def get_parent_from_tree(self, address):
        queue = [self]
        while len(queue) > 0:
            node = queue.pop(0)
            if node.address == address:
                return node.parent
            for child in node.children:
                queue.append(child)

        return None


    def search_for_childless(self, node_address):
        parent_addr = self.get_parent_from_tree(node_address)
        if parent_addr is not None:

            return parent_addr

        queue = [self]
        while len(queue) > 0:
            node = queue.pop(0)
            if node.can_hold_children():
                return node
            for child in node.children:
                queue.append(child)

        return None


    def __str__(self):
        return self.address
