"""
Controller class to handle game logic.
"""

from abc import ABC, abstractmethod

class ChessController(ABC):
    """
    Abstract Base Class. Defines methods to be implemented in Controller.
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
    def move(self):
        """
        Abstract method to be implemented in Controller.
        """


class Controller(ChessController):
    pass