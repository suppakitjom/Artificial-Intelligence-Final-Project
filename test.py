import numpy as np
import random
from collections import deque

random.seed(0)  # For reproducibility, can be removed for more varied outcomes
player_dict = {0: 'X', 1: 'Y'}

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
                
    def print_board(self, players=[]):
        display_board = np.where(self.board == 1, "o", " ").astype(str)
        for num, player in enumerate(players):
            row, col = player.position
            display_board[row, col] = player_dict[num]
        
        board_str = "+" + "---+" * self.size + "\n"
        for row in display_board:
            row_str = "| " + " | ".join(row) + " |\n"
            board_str += row_str + "+" + "---+" * self.size + "\n"
        print(board_str)
    
    def get_coins_left(self):
        return np.sum(self.board)
    
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

class Player:
    def __init__(self, start_position, score=0):
        self.position = start_position
        self.score = score

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
        self.current_player = 0  # Player X starts
        self.size = size
        # Recognize if an agent spawns on a coin and adjust scores accordingly
        for player in self.players:
            if self.board.board[player.position] == 1:
                player.score += 1
                self.board.board[player.position] = 0  # Remove the coin as it's collected
        print("Initial Board:")
        self.board.print_board(self.players)  # Print the initial board state

    def play_game(self):
        rounds = 0
        # The initial board is already printed in __init__, so we can directly start the game loop
        while self.board.get_coins_left() > 0:
            player = self.players[self.current_player]
            best_score, best_move = self.minimax(3, self.current_player, True, -float('inf'), float('inf'))
            if best_move:
                prev_score = player.score
                self.apply_move(best_move, player)
                rounds += 1
                # Print each move
                print(f"Round {rounds}: Player {player_dict[self.current_player]} moves {best_move}.", end=" ")
                if player.score > prev_score:
                    print(f"Collected a coin! Total score: {player.score}.", end=" ")
                    if (player.score - prev_score) > 1:  # Checks for bonus
                        print(f"Bonus applied! (+{player.score - prev_score - 1})", end=" ")
                print("\nBoard after move:")
                self.board.print_board(self.players)
            self.current_player = 1 - self.current_player  # Switch players

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
        best_score, best_move = self.minimax(depth, self.current_player, True, -float('inf'), float('inf'))
        if best_move:
            self.apply_move(best_move, self.players[self.current_player])

    def minimax(self, depth, player_index, is_maximizing, alpha, beta):
        if depth == 0 or self.board.get_coins_left() == 0:
            return self.evaluate(player_index,self.board), None
        
        for move in self.players[player_index].get_valid_moves(self.board, self.players):
            if self.board.board[self.players[player_index].position[0] + move[0],
                                self.players[player_index].position[1] + move[1]] == 1:
                # Assign a high score for immediate coin collection
                return (float('inf'), move) if is_maximizing else (-float('inf'), move)
        
        best_move = None
        if is_maximizing:
            max_eval = -float('inf')
            equal_moves = []
            for move in self.players[player_index].get_valid_moves(self.board,self.players):
                new_board, new_player = self.simulate_move(move, player_index)
                evaluation = self.minimax(depth - 1, 1 - player_index, False, alpha, beta)[0]
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
            for move in self.players[player_index].get_valid_moves(self.board,self.players):
                new_board, new_player = self.simulate_move(move, player_index)
                evaluation = self.minimax(depth - 1, 1 - player_index, True, alpha, beta)[0]
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


    def simulate_move(self, move, player_index):
        # Simulate a move without affecting the current game state
        new_board = GameBoard(self.size, self.board.board)
        new_player = Player(self.players[player_index].position, self.players[player_index].score)
        self.apply_move(move, new_player, new_board)
        return new_board, new_player

    def apply_move(self, move, player, board=None):
        if board is None:
            board = self.board
        new_position = (player.position[0] + move[0], player.position[1] + move[1])
        player.position = new_position
        if board.board[new_position] == 1:
            player.score += 1
            board.board[new_position] = 0

game = Game(size=8)
game.play_game()