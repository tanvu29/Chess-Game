"""
Main file to run the Chess game.
"""

from chess_model import ChessModel
from chess_view import PygameChessView
from chess_controller import GameController


def main():
    """
    Main function to run the Chess game.
    """
    model = ChessModel()
    view = PygameChessView(model)
    controller = GameController(model, view)
    controller.run()


if __name__ == "__main__":
    main()
