"""this is to test inheritance -- Child
"""

from parent import Parent
from utils import welcome, goodbye


class Child(Parent):
    """trivial child class"""

    def __init__(self):
        Parent.__init__(self)

        self.code = 0
        self.name = 'child'

    def be_silent(self):
        """supposed to be silent"""
        goodbye(self.code)
        welcome(self.code)
