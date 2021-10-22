from anytree import NodeMixin, AnyNode, TreeError
import logging

class OrderedNodeMixin(NodeMixin):
    def move_left(self, distance=1):
        self.insert_or_move(-distance, None)

    def move_right(self, distance=1):
        self.insert_or_move(distance, None)

    @property
    def index(self):
        if self.is_root:
            return 0

        return list(self.parent.children).index(self)

    # when inserting `node` (node is not None)
    # 0 = before `self`, -1 = two before `self`
    # 1 = after self, 2 = two after self
    # and so on
    #
    # when moving `self` (node is None)
    # 0: nothing
    # negative: in left direction (before)
    # positive: in right direction (after)
    def insert_or_move(self, distance, node):
        if self.is_root:
            raise TreeError("Cannot insert or move nodes on root level")

        parentchildren = list(self.parent.children)
        index = parentchildren.index(self)

        # when moving 
        if node is None:
            parentchildren.remove(self)
            node = self

        if distance + index > len(parentchildren):
            raise IndexError("Index out of range of existing siblings")
        
        if distance + index < 0:
            raise IndexError("Index out of range")

        parentchildren.insert(index + distance, node)
        self.parent.children = parentchildren

    def insert_left(self, node):
        self.insert_or_move(0, node)

    def insert_right(self, node):
        self.insert_or_move(1, node)

    def insert_left_of(self, node):
        if not isinstance(node, OrderedNodeMixin):
            raise ValueError("Node is not of type OrderedNodeMixin")

        node.insert_left(self)

    def insert_right_of(self, node):
        if not isinstance(node, OrderedNodeMixin):
            raise ValueError("Node is not of type OrderedNodeMixin")

        node.insert_right(self)

    @property
    def left(self):
        index = self.parent.children.index(self)
        if index == 0:
            return None
        else:
            return self.parent.children[index - 1]

    @property
    def right(self):
        index = self.parent.children.index(self)
        if index == len(self.parent.children) - 1:
            return None
        else:
            return self.parent.children[index + 1]

    def sort_children(self, key=None):
        children = list(self.children)
        children.sort(key=key)
        self.children = children


class LinkedListNodeMixin(NodeMixin):
    @property
    def link_index(self):
        i = 0
        it = self._link_prev

        if it is None:
            return i

        i += 1
        while it._link_prev is not None:
            assert it != it._link_prev
            it = it._link_prev
            i += 1

        return i

    @property
    def index(self):
        if self.is_root:
            return 0

        return list(self.parent.children).index(self)

    def sort_children_link(self, reverse=False):
        self.sort_children(key=lambda node: node.link_index, reverse=reverse)

    def sort_tree_link(self, reverse=False):
        self.sort_tree(key=lambda node: node.link_index, reverse=reverse)
    
    def sort_children(self, key=None, reverse=False):
        for child in self.children:
            child._block_hooks = True

        children = list(self.children)
        children.sort(key=key, reverse=reverse)
        self.children = children

        for child in self.children:
            child._block_hooks = False

    def sort_tree(self, key=None, reverse=False):
        self.sort_children(key=key, reverse=reverse)

        for child in self.children:
            child.sort_tree(key=key, reverse=reverse)

    def move_backwards(self):
        self._link_prev.insert_before(self)

    def move_forwards(self):
        self._link_next.insert_after(self)

    def _insert_prepare(self, node):
        if not isinstance(node, LinkedListNodeMixin):
            raise ValueError("Node is not of type OrderedNodeMixin")

        if self == node:
            raise TreeError("Cannot insert self before or after itself")

        node.parent = self.parent
        node.remove_from_linked_list()

    # insert the given node before/after this node
    def insert_before(self, node):
        self._insert_prepare(node)

        node._link_prev = self._link_prev
        if not self._link_prev is None:
            self._link_prev._link_next = node
        self._link_prev = node
        node._link_next = self

    def insert_after(self, node):
        self._insert_prepare(node)

        node._link_next = self._link_next
        if not self._link_next is None:
            self._link_next._link_prev = node
        self._link_next = node
        node._link_prev = self

    def insert(self, node, before=True):
        if before:
            self.insert_before(node)
        else:
            self.insert_after(node)

    # inserts this node before/after the given one
    def insert_self(self, node, before=True):
        if not isinstance(node, LinkedListNodeMixin):
            raise ValueError("Node is not of type OrderedNodeMixin")

        if before:
            node.insert_before(self)
        else:
            node.insert_after(self)

    @property
    def _link_next(self):
        try:
            return self.__link_next
        except AttributeError:
            return None

    @_link_next.setter
    def _link_next(self, value):
        self.__link_next = value
        
    @property
    def _link_prev(self):
        try:
            return self.__link_prev
        except AttributeError:
            return None

    @_link_prev.setter
    def _link_prev(self, value):
        if value == self:
            logging.debug("setting link_prev of {} to itself, creating a loop".format(self.title))
            raise TreeError("Setting a link loop")
        self.__link_prev = value

    @property
    def next(self):
        return self._link_next

    @property
    def prev(self):
        return self._link_prev

    @property
    def first_link(self):
        it = self._link_prev

        if it is None:
            return self

        while not it._link_prev is None:
            assert it != it._link_prev
            it = it._link_prev

        return it

    @property
    def last_link(self):
        it = self._link_next

        if it is None:
            return self

        while not it._link_next is None:
            assert it != it._link_next
            it = it._link_next

        return it

    @property
    def first_link_child(self):
        if len(self.children) == 0:
            return None

        return self.children[0].first_link

    @property
    def last_link_child(self):
        if len(self.children) == 0:
            return None

        return self.children[0].last_link

    def insert_as_first_child(self, node):
        if self == node:
            raise TreeError("Cannot insert node as its own child")

        if self.first_link_child is None:
            node.parent = self
        else:
            self.first_link_child.insert_before(node)

    def insert_as_last_child(self, node):
        if self == node:
            raise TreeError("Cannot insert node as its own child")

        if self.last_link_child is None:
            node.parent = self
        else:
            self.last_link_child.insert_after(node)

    def remove_from_linked_list(self):
        if not self._link_prev is None:
            self._link_prev._link_next = self._link_next

        if not self._link_next is None:
            self._link_next._link_prev = self._link_prev

    @property
    def _block_hooks(self):
        try:
            return self.__block_hooks
        except AttributeError:
            return False

    @_block_hooks.setter
    def _block_hooks(self, value):
        self.__block_hooks = value


    def _post_detach(self, parent):
        if self._block_hooks:
            return
        self.remove_from_linked_list()

    def _pre_attach(self, parent):
        if self._block_hooks:
            return

        self._link_next = None
        if not parent.last_link_child is None:
            self._link_prev = parent.last_link_child
            parent.last_link_child._link_next = self
            

class AnyOrderedNode(AnyNode, OrderedNodeMixin):
    pass

class AnyLinkedListNode(AnyNode, LinkedListNodeMixin):
    pass

class AnyTaskTreeAwareNode(AnyLinkedListNode):
    def __init__(self, tasktree):
        super().__init__()
        self.tasktree = tasktree

