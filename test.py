import numpy as np
import random
from collections import deque

random.seed(0)  # For reproducibility, can be removed for more varied outcomes
player_dict = {0: 'X', 1: 'Y'}
SEARCH_DEPTH = 3

class GameBoard:
    def __init__(self, size=8, board=None):
        self.size = size
        if board is None:
            self.board = np.zeros((size, size), dtype=int)
            for row in range(size):
                for col in range(size):
                    self.board[row, col] = random.randint(0, 1)  # Randomly place coins
        else:
            self.board = np.copy(board)  # Use an existing board state

    def print_board(self, players = []):
        '''
        Print the game board with players and coins.
        Takes an optional list of Player objects to display player positions and scores.
        '''
        # Define symbols for readability
        empty_cell_symbol = " "
        coin_cell_symbol = "●"
        transparent_coin_symbol = "○"
        
        display_board = np.full((self.size, self.size), empty_cell_symbol, dtype=str)
        # Mark coins on the display board
        for row in range(self.size):
            for col in range(self.size):
                if self.board[row, col] == 1:
                    display_board[row, col] = coin_cell_symbol
                elif self.board[row, col] == 2:
                    display_board[row, col] = transparent_coin_symbol
                    
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
    
    def get_coins_left(self):
        return np.sum(self.board != 0)
    
    def nearest_coin_distance(self, start_pos):
        if self.board[start_pos] == 1:
            return 0  # Standing on a coin
        
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]  # Down, Up, Right, Left
        visited = set([start_pos])
        queue = deque([(start_pos, 0)])  # (position, distance)
        
        while queue:
            (current_pos, distance) = queue.popleft()
            for direction in directions:
                next_pos = (current_pos[0] + direction[0], current_pos[1] + direction[1])
                if (0 <= next_pos[0] < self.size and 0 <= next_pos[1] < self.size
                        and next_pos not in visited):
                    if self.board[next_pos] == 1:
                        return distance + 1
                    queue.append((next_pos, distance + 1))
                    visited.add(next_pos)
        return float('inf')  # In case no coins are found
    
    def is_move_valid(self, row, col, players):
        """
        Check if a move is valid: inside the board and not occupied by another player.
        """
        if 0 <= row < self.size and 0 <= col < self.size:
            # Ensure no player is at the new position
            return not any(player.position == (row, col) for player in players)
        return False

    def transparent_coin(self):
        '''
        Every coin has a 50% chance to go transparent and be uncollectable,
        and every transparent coin has a 50% chance to go back to normal
        '''

        for row in range(self.size):
            for col in range(self.size):
                if self.board[row, col] == 1:
                    if random.random() < 0.5:
                        self.board[row, col] = 2
                elif self.board[row, col] == 2:
                    if random.random() < 0.5:
                        self.board[row, col] = 1

class Player:
    def __init__(self, start_position, score=0):
        self.position = start_position
        self.score = score
        self.consecutive_coins = 0  

    def get_valid_moves(self, board, players):
        """
        Only return moves that do not result in collisions.
        """
        valid_moves = []
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]  # Right, left, down, up
        for dr, dc in directions:
            new_row, new_col = self.position[0] + dr, self.position[1] + dc
            if board.is_move_valid(new_row, new_col, players):
                valid_moves.append((dr, dc))
        return valid_moves

class Game:
    def __init__(self, size=8):
        self.board = GameBoard(size)
        self.players = [Player((0, 0)), Player((size - 1, size - 1))]
        self.player_index = 0  # Player X starts
        self.size = size
        
        print("Initial Board:")
        self.board.print_board()  # Print the initial board state

    def play_game(self):
        rounds = 0
        # Recognize if an agent spawns on a coin and adjust scores accordingly
        for player in self.players:
            if self.board.board[player.position] == 1:
                player.score += 1
                player.consecutive_coins += 1
                self.board.board[player.position] = 0  # Remove the coin as it's collected

        move_dict = {(0, 1): 'right', (0, -1): 'left', (1, 0): 'down', (-1, 0): 'up'}
        while self.board.get_coins_left():
            self.board.transparent_coin()
            player = self.players[self.player_index]
            best_score, best_move = self.minimax(depth=SEARCH_DEPTH, player_index=self.player_index, is_maximizing=True, alpha=-float('inf'), beta=float('inf'), board=self.board, players=self.players)
            if best_move:
                prev_score = player.score
                self.apply_move(best_move, player)
                rounds += 1
                # Print each move
                print(f"Round {rounds}: Player {player_dict[self.player_index]} moves {move_dict[best_move]}.", end=" ")
                if player.score > prev_score:
                    print(f"Collected a coin! Total score: {player.score}.", end=" ")
                    if player.consecutive_coins:
                        print(f"({player.consecutive_coins} consecutive coin(s))", end=" ")
                    if (player.score - prev_score) > 1:  # Checks for bonus
                        print(f"Bonus applied! (+{player.score - prev_score - 1})", end=" ")
                print("\nBoard after move:")
                self.board.print_board(self.players)
            self.player_index = 1 - self.player_index  # Switch players

        # Summarize game results at the end
        self.summarize_game(rounds)

    # Final scores and winner announcement
    def summarize_game(self, rounds):
        print(f"\nFinal Scores after {rounds} rounds:")
        scores = [(player.score, idx) for idx, player in enumerate(self.players)]
        scores.sort(reverse=True)
        for score, idx in scores:
            print(f"Player {player_dict[idx]}: {score}")
        if scores[0][0] == scores[1][0]:
            print("It's a draw!")
        else:
            print(f"Player {player_dict[scores[0][1]]} wins!")

    def minimax_move(self, depth=5):
        best_score, best_move = self.minimax(depth, self.player_index, True, -float('inf'), float('inf'))
        if best_move:
            self.apply_move(best_move, self.players[self.player_index])

    def minimax(self, depth, player_index, is_maximizing, alpha, beta, board, players):
        if depth == 0 or board.get_coins_left() == 0:
            return self.evaluate(player_index, board), None
        
        best_move = None
        if is_maximizing:
            max_eval = -float('inf')
            equal_moves = []
            for move in players[player_index].get_valid_moves(board, players):
                new_board, new_players = self.simulate_move(move, player_index, board, players)
                evaluation, _ = self.minimax(depth - 1, 1 - player_index, False, alpha, beta, new_board, new_players)
                if evaluation > max_eval:
                    max_eval = evaluation
                    equal_moves = [move]
                elif evaluation == max_eval:
                    equal_moves.append(move)
                alpha = max(alpha, evaluation)
                if beta <= alpha:
                    break
            best_move = random.choice(equal_moves) if equal_moves else None
            return max_eval, best_move
        else:
            min_eval = float('inf')
            for move in players[player_index].get_valid_moves(board, players):
                new_board, new_players = self.simulate_move(move, player_index, board, players)
                evaluation, _ = self.minimax(depth - 1, 1 - player_index, True, alpha, beta, new_board, new_players)
                if evaluation < min_eval:
                    min_eval = evaluation
                    best_move = move
                beta = min(beta, evaluation)
                if beta <= alpha:
                    break
            return min_eval, best_move

    def evaluate(self, player_index, board):
        player = self.players[player_index]
        opponent = self.players[1 - player_index]

        # Score difference is crucial but should not be the only factor.
        score_diff = player.score - opponent.score

        # Calculate the nearest coin distance for both players and prefer smaller distances.
        player_dist = board.nearest_coin_distance(player.position)
        opponent_dist = board.nearest_coin_distance(opponent.position)

        # Inverting the distance so that smaller distances are better.
        # Adding a small constant to prevent division by zero.
        player_advantage = 1 / (player_dist + 0.1)
        opponent_advantage = 1 / (opponent_dist + 0.1)

        # Calculating the net advantage.
        proximity_advantage = player_advantage - opponent_advantage

        # You might need to adjust the weights to find what works best for your game.
        return score_diff + proximity_advantage


    def simulate_move(self, move, player_index, board, players):
        # Clone the board
        new_board = GameBoard(board.size, board.board)
        
        # Deep copy the players to prevent state leakage
        new_players = [Player(p.position, p.score) for p in players]
        new_player = new_players[player_index]
        
        # Apply the move
        new_position = (new_player.position[0] + move[0], new_player.position[1] + move[1])
        new_player.position = new_position
        if new_board.board[new_position] == 1:
            new_player.score += 1
            new_player.consecutive_coins += 1
            new_board.board[new_position] = 0
            if new_player.consecutive_coins >= 3:
                bonus = new_player.consecutive_coins ** 2
                new_player.score += bonus - new_player.consecutive_coins
        else:
            new_player.consecutive_coins = 0
        
        return new_board, new_players



    def apply_move(self, move, player, board=None):
        if board is None:
            board = self.board
        new_position = (player.position[0] + move[0], player.position[1] + move[1])
        player.position = new_position
        if board.board[new_position] == 1:
            player.score += 1
            player.consecutive_coins += 1
            board.board[new_position] = 0
            if player.consecutive_coins >= 3:
                bonus = player.consecutive_coins ** 2
                player.score += bonus
        else:
            player.consecutive_coins = 0



game = Game(size=8)
game.play_game()
