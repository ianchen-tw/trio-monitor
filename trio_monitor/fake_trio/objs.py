from typing import Dict, List, Optional, Union

from rich.console import Console, ConsoleOptions, RenderResult
from rich.tree import Tree


class Nursery:
    """Represent the trio internal type.

    The only usable attribute is `self.child_tasks`
    """

    def __init__(self, name: str):
        self.child_tasks: List["Task"] = []
        self._name: str = name
        self._tree_root: Optional["Task"] = None

    @property
    def tree_root(self):
        return self._tree_root

    @tree_root.setter
    def tree_root(self, new_root: "Task"):
        if self._tree_root != new_root:
            self._tree_root = new_root
            self._tree_root.register(self)
            for t in self.child_tasks:
                t.tree_root = self._tree_root

    def _add_task(self, task: "Task"):
        if task not in self.child_tasks:
            self.child_tasks.append(task)
            if self._tree_root:
                task.tree_root = self.tree_root

    def __repr__(self):
        if len(self.child_tasks) > 0:
            return f"<Nursery {self.child_tasks}>"
        return f"Nursery"

    @property
    def rich_tag(self):
        ret = "[bold magenta]Nursery"
        if self._name is not None:
            ret += f": [white]{self._name}"
        return ret

    def _rich_node(self, parent: Tree):
        cur_node = parent.add(self.rich_tag)
        for t in self.child_tasks:
            t._rich_node(parent=cur_node)


class Task:
    """Represent the trio internal type

    The only usable attribute is `self.child_nurseries`
    """

    def __init__(self, name: str, tree_root: Optional["Task"] = None):
        self.child_nurseries: List[Nursery] = []
        self._name: str = name

        # Each node would register itself with to root node's dict, so we could referece
        # node by it's name
        self._tree_root: "Task" = self if tree_root is None else tree_root
        self.nodes: Dict[
            str, Union["Task", "Nursery"]
        ] = {}  # only used by the tree root node

        if self.is_root:
            self.register(self)

    @property
    def tree_root(self) -> "Task":
        return self._tree_root

    @tree_root.setter
    def tree_root(self, new_root: Optional["Task"]):
        if new_root is not None:
            if self.is_root:
                self.nodes.clear()
            self._tree_root = new_root
            self._tree_root.register(self)
            for n in self.child_nurseries:
                n.tree_root = new_root
        else:
            # become a new root
            if not self.is_root:
                del self._tree_root.nodes[self._name]
            self._tree_root = self
            for n in self.child_nurseries:
                n.tree_root = self

    def _add_nursery(self, nursery: "Nursery"):
        if nursery not in self.child_nurseries:
            self.child_nurseries.append(nursery)
            nursery.tree_root = self.tree_root

    def register(self, node: Union[Nursery, "Task"]):
        if not self.is_root:
            raise RuntimeError("Could only call register on a root task")
        if node._name in self.nodes:
            raise ValueError(f"Registered name already exists: {node._name}")
        self.nodes[node._name] = node

    def __repr__(self):
        if len(self.child_nurseries) > 0:
            return f"<Task {self.child_nurseries}>"
        return "<Task>"

    @property
    def is_root(self) -> bool:
        return self == self.tree_root

    @property
    def rich_tag(self):
        ret = "[bold yellow]Task"
        if self._name is not None:
            ret += f": [white]{self._name}"
        return ret

    def _rich_node(self, parent: Tree):
        cur_node = parent.add(self.rich_tag)
        [n._rich_node(parent=cur_node) for n in self.child_nurseries]

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        """Support Python `rich` lib"""
        root = Tree(self.rich_tag)
        [n._rich_node(parent=root) for n in self.child_nurseries]
        yield root


def gen_tree_from_json(dic: Dict) -> Task:
    """Generate a trio task tree based on dict provided"""

    def build_task(task: Dict) -> Task:
        t = Task(name=task.get("name", None))
        for n in task["nurseries"]:
            t._add_nursery(build_nursery(n))
        return t

    def build_nursery(nursery: Dict) -> Nursery:
        n = Nursery(name=nursery.get("name", None))
        for t in nursery["tasks"]:
            n._add_task(build_task(t))
        return n

    return build_task(dic)
