import numpy as np
import random
from collections import deque

# random.seed(0)
player_dict = {0:'X', 1:'Y'}

class GameBoard:
    '''
    Class to represent the game board.
    Contains methods to initialize the board, print the board, check move validity, and find the nearest coin.
    '''
    def __init__(self, size=8):
        '''
        Initialize the game board with a given size and randomly place coins on the board.
        '''
        self.size = size
        self.board = np.zeros((size, size), dtype=int)
        for row in range(size):
            for col in range(size):
                self.board[row, col] = random.randint(0, 1)  # Randomly place coins
                
    # def print_board(self, players):
    #     display_board = np.copy(self.board).astype(str)
    #     for num, player in enumerate(players):
    #         row, col = player.position
    #         display_board[row, col] = player_dict[num]  # Distinguish players on the board
        
    #     for row in display_board:
    #         print(" ".join(row))
    #     print()

    def print_board(self, players = []):
        '''
        Print the game board with players and coins.
        Takes an optional list of Player objects to display player positions and scores.
        '''
        # Define symbols for readability
        empty_cell_symbol = " "
        coin_cell_symbol = "o"
        
        display_board = np.full((self.size, self.size), empty_cell_symbol, dtype=str)
        # Mark coins on the display board
        for row in range(self.size):
            for col in range(self.size):
                if self.board[row, col] == 1:
                    display_board[row, col] = coin_cell_symbol
                    
        # Place players on the board
        for num, player in enumerate(players):
            row, col = player.position
            display_board[row, col] = player_dict[num]
    
        board_str = "+" + "---+" * self.size + "\n"
        for row in display_board:
            row_str = "| " + " | ".join(row) + " |\n"
            board_str += row_str + "+" + "---+" * self.size + "\n"
        print(board_str,end='')
        if players:
            print(f"Coins left: {self.get_coins_left()}")
            print(f"Player X score: {players[0].score}")
            print(f"Player Y score: {players[1].score}")
        print()


    def is_move_valid(self, row, col, players):
        '''
        Takes input of row and column and a list of Player objects.
        Returns True if the move is valid (position inside the board and no other player is present), False otherwise.
        '''
        if 0 <= row < self.size and 0 <= col < self.size:
            return not any(player.position == (row, col) for player in players)
        return False
    
    def get_coins_left(self):
        '''
        Returns the number of coins left on the board.
        '''
        return np.sum(self.board)
    
    def nearest_coin_distance(self, position, players):
        '''
        Takes a position tuple (row, column) and a list of Player objects.
        Returns the distance to the nearest coin from the given position using BFS.
        '''
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        visited = set()
        queue = deque([(position, 0)])  # (position, distance)

        while queue:
            (current_row, current_col), distance = queue.popleft()
            if (current_row, current_col) not in visited:
                visited.add((current_row, current_col))
                
                # Check if current position has a coin
                if self.board[current_row, current_col] == 1:
                    return distance
                
                # Add valid adjacent positions to the queue
                for dr, dc in directions:
                    new_row, new_col = current_row + dr, current_col + dc
                    if self.is_move_valid(new_row, new_col, players):
                        queue.append(((new_row, new_col), distance + 1))
        return float('inf')
    
class Player:
    '''
    Class to represent a player in the game.
    Contains methods to get valid moves, evaluate moves, and make a move on the board.
    '''
    def __init__(self, start_position):
        '''
        Initialize the player with a starting position.
        Score and Consecutive coins are set to 0.
        '''
        self.position = start_position
        self.score = 0
        self.consecutive_coins = 0  

    def get_valid_moves(self, board, players):
        '''
        Returns a list of legal moves for the player based on the current board state.
        '''
        valid_moves = []
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)] # Right, left, down, up
        for dr, dc in directions:
            new_row, new_col = self.position[0] + dr, self.position[1] + dc
            if board.is_move_valid(new_row, new_col, players):
                valid_moves.append((dr, dc))
        return valid_moves

    def evaluate_moves(self, board, players):
        '''
        Evaluates the valid moves for the player and returns the best move based on the nearest coin.
        '''
        valid_moves = self.get_valid_moves(board, players)

        best_score = -float('inf')
        best_move = None
        current_position = np.array(self.position)

        for move in valid_moves:
            new_position = tuple(current_position + move)

            # Check if the move results in immediate scoring
            if board.board[new_position] == 1:
                score = float('inf')
            else:
                # Calculate the distance to the nearest coin after the move
                distance_to_coin = board.nearest_coin_distance(new_position,players)
                # Score prioritizes moves with shorter distances to coins
                score = 1 / (distance_to_coin + 1)  # Add 1 to avoid division by zero

            # Prioritize moves with higher scores
            if score > best_score:
                best_score = score
                best_move = move

        return best_move

    def move(self, board, players):
        '''
        Makes a move for the player on the board based on the evaluation of valid moves.
        '''
        best_move = self.evaluate_moves(board, players)
        if best_move:
            self.position = tuple(np.array(self.position) + best_move)
            return best_move
        return False

class Game:
    '''
    Class to represent the game.
    Contains methods to initialize the game, play the game, and summarize the game results.
    '''

    def __init__(self):
        '''
        Initialize the game with a GameBoard and two Player objects spawned at each corner of the board.
        '''
        self.board = GameBoard()
        self.players = [Player((0, 0)), Player((7, 7))]
        self.rounds = 0
        print("Initial Board:")
        self.board.print_board()
    
    def play_game(self):
        '''
        Play the game until all coins are collected.
        Alternate between players to make moves and update the board.
        '''

        move_dict = {(0, 1): 'right', (0, -1): 'left', (1, 0): 'down', (-1, 0): 'up'}

        for player in self.players: # Check if players are starting on coins
            row, col = player.position
            if self.board.board[row, col] == 1:
                player.score += 1
                self.board.board[row, col] = 0 

        print("Game Start!")
        self.board.print_board(self.players)

        player_index = 0

        while self.board.get_coins_left():  # Continue until all coins are collected
            player = self.players[player_index]
            selected_move = player.move(self.board, self.players)

            row, col = player.position
            if self.board.board[row, col] == 1:
                player.score += 1
                player.consecutive_coins += 1
                self.board.board[row, col] = 0

                if player.consecutive_coins >=3: # Take in account the current coin streak and apply bonus accordingly
                    bonus = player.consecutive_coins ** 2
                    player.score += bonus - player.consecutive_coins 
                    print(f"Bonus! Player {player_dict[player_index]} collected {player.consecutive_coins} consecutive coins for a bonus of {bonus - player.consecutive_coins} points!")
            else:
                player.consecutive_coins = 0
            print(f"Player {player_dict[player_index]} moved {move_dict[selected_move]}",f"({player.consecutive_coins} consecutive coin(s))" if player.consecutive_coins else "")

            self.board.print_board(self.players)

            player_index = 1 - player_index # Alternate between players
            self.rounds += 1

        self.summarize_game()

    def summarize_game(self):
        '''
        Print the final scores of the game and declare the winner.
        '''
        print(f"\nFinal Scores ({self.rounds} rounds):")
        for num, player in enumerate(self.players):
            print(f"Player {player_dict[num]}: {player.score}")
        
        if self.players[0].score == self.players[1].score:
            print("Game Over. It's a draw!")
        else:
            winner = max(self.players, key=lambda p: p.score)
            print(f"Game Over. The winner is Player {player_dict[self.players.index(winner)]} with score of {winner.score}")

game = Game()
game.play_game()
