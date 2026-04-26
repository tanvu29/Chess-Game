from ChessModel import ChessModel
from ChessView import PygameChessView
from chess_controller import GameController


def main():
    model = ChessModel()
    view = PygameChessView(model)
    controller = GameController(model, view)
    controller.run()


if __name__ == "__main__":
    main()
