MINIMAX = 0

if MINIMAX:
    from minimax import Game
    game = Game()
    game.play_game()
else:
    from normal import Game
    game = Game()
    game.play_game()

