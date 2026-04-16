"""
View class to display GUI of the game.
"""

from abc import ABC, abstractmethod

class ChessView(ABC):
    """
    Abstract Base Class. Defines methods to be implemented in View.
    """

    def __init__(self, board):
        self._board = board

    @property
    def board(self):
        """
        Property method that returns a board instance.
        """
        return self._board

    @abstractmethod
    def display(self):
        """
        Abstract method to be implemented in View.
        """

class View():
    pass