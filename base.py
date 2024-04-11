import numpy as np
import random

random.seed(0)
player_dict = {0:'X', 1:'Y'}

class GameBoard:
    def __init__(self, size=8):
        self.size = size
        self.board = np.zeros((size, size), dtype=int)
        for row in range(size):
            for col in range(size):
                self.board[row, col] = random.randint(0, 1)  # Randomly place coins
                
    def print_board(self, players):
        display_board = np.copy(self.board).astype(str)
        for num, player in enumerate(players):
            row, col = player.position
            display_board[row, col] = player_dict[num]  # Distinguish players on the board
        
        for row in display_board:
            print(" ".join(row))
        print()
        
    def is_move_valid(self, row, col, players):
        if 0 <= row < self.size and 0 <= col < self.size:
            return not any(player.position == (row, col) for player in players)
        return False
    
    def get_coins_left(self):
        return np.sum(self.board)
    
class Player:
    def __init__(self, start_position):
        self.position = start_position
        self.score = 0

    def get_valid_moves(self, board, players):
        valid_moves = []
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)] # Right, left, down, up
        for dr, dc in directions:
            new_row, new_col = self.position[0] + dr, self.position[1] + dc
            if board.is_move_valid(new_row, new_col, players):
                valid_moves.append((dr, dc))
        # print(f"Valid moves for player at {self.position}: {valid_moves}")  # Debug statement
        return valid_moves

    def move(self, board, players):
        valid_moves = self.get_valid_moves(board, players)
        if valid_moves:
            move = random.choice(valid_moves)
            self.position = (self.position[0] + move[0], self.position[1] + move[1])
            return move
        return False

class Game:
    def __init__(self):
        self.board = GameBoard()
        self.players = [Player((0, 0)), Player((7, 7))]
        print("Game Starting:")
        self.board.print_board(self.players)
    
    def play_game(self):
        move_dict = {(0, 1): 'right', (0, -1): 'left', (1, 0): 'down', (-1, 0): 'up'}

        for player in self.players: # Check if players are starting on coins
                row, col = player.position
                if self.board.board[row, col] == 1:
                        player.score += 1
                        self.board.board[row, col] = 0 
        player_index = 0
        while self.board.get_coins_left():  # Continue until all coins are collected
            player = self.players[player_index]
            selected_move = player.move(self.board, self.players)
            if selected_move:
                print(f"Player {player_dict[player_index]} moved {move_dict[selected_move]}")
                row, col = player.position
                if self.board.board[row, col] == 1:
                    player.score += 1
                    self.board.board[row, col] = 0
            self.board.print_board(self.players)
            player_index = 1 - player_index
        
        print("\nFinal Scores:")
        for num, player in enumerate(self.players):
            print(f"Player {player_dict[num]}: {player.score}")
        print("Game Over.")


game = Game()
game.play_game()