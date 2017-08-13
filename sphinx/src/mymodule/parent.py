"""This is to test inheritance -- Parent
"""

from utils import welcome, goodbye


class Parent(object):
    """Trivial parent class"""

    def __init__(self):
        self.code = 0
        self.name = 'parent'

    def speak(self):
        """supposed to speak"""
        welcome(self.name)
        goodbye(self.name)
