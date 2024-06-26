import numpy as np
import random
from collections import deque
import math
from controller import Supervisor

random.seed(0)
player_dict = {0: 'X', 1: 'Y'}
SEARCH_DEPTH = 3

class Sim(Supervisor):
    '''
    Class to control the simulation environment.
    Contains methods to create and remove coins, and move the robot on the board.
    '''
    def __init__(self):
        '''
        Creates the supervisor instance
        '''
        self.game = Supervisor()
        self.timestep = int(self.game.getBasicTimeStep())
        self.arena = self.game.getFromDef('arena')

    def get_x_y(self,row,column):
        '''
        Function to convert the row and column indices to x and y coordinates on the board.
        '''
        x_offset = 0.35
        y_offset = -0.35
        tile_size = 0.1
        floor_size = self.arena.getField('floorSize').getSFVec2f()

        center_x = -floor_size[0] / 2 + x_offset
        center_y = -floor_size[1] / 2 + y_offset
        x = center_x + (column + 0.5) * tile_size
        y = center_y + (7 - row + 0.5) * tile_size
        return x,y

    def create_coin(self,row,column):
        '''
        Function to spawn a coin on the board at a given row and column.
        the coin is defined as a DEF node in the Webots world file.
        the DEF name is coin_{row}_{column}
        '''
        x, y = self.get_x_y(row=row,column=column)
        coin_def = f"coin_{row}_{column}"
        coin_def_string = f'DEF {coin_def} Coin {{ translation {x} {y} 0.025 name "{coin_def}" }}'
        root_node = self.game.getRoot()
        children_field = root_node.getField('children')
        children_field.importMFNodeFromString(-1, coin_def_string)

    def remove_coin(self,row,column):
        '''
        Function to remove a coin from the board at a given row and column.
        '''
        coin_name = f"coin_{row}_{column}"
        print(f"Removing coin {coin_name}")
        coin_node = self.game.getFromDef(coin_name)
        coin_node.remove()

    def set_coin_transparency(self,row,column,state):
        '''set color to black if state = 2, yellow if 1'''
        coin_name = f"coin_{row}_{column}"
        coin_node = self.game.getFromDef(coin_name)
        coin_color = coin_node.getField('color')
        if state == 1:
            coin_color.setSFColor([1, .823, 0])
        elif state == 2:
            coin_color.setSFColor([0, 0, 0])
        pass 

    def move_robot(self,robot_def,row,column,direction):
        '''
        Function to simulate the movement of the robot on the board.
        The robot is moved to the given row and column and turned in the specified direction.
        '''
        rotation = {'left':math.pi, 'right':0, 'up':math.pi/2, 'down':-math.pi/2}
        robot = self.game.getFromDef(robot_def)
        x, y = self.get_x_y(row=row,column=column)
        # turn the robot to the correct direction
        rotation_field = robot.getField('rotation')
        rotation_field.setSFRotation([0, 0, 1, rotation[direction]])

        translation_field = robot.getField('translation')
        current_position = translation_field.getSFVec3f()
        target_position = [x, y, 0]
        num_iterations = 15
        step_size = [(target_position[i] - current_position[i]) / num_iterations for i in range(3)]
        for _ in range(num_iterations):
            current_position = [current_position[i] + step_size[i] for i in range(3)]
            translation_field.setSFVec3f(current_position)
            self.game.step(self.timestep)


class GameBoard:
    def __init__(self, size=8, board=None):
        self.size = size
        if board is None:
            self.board = np.zeros((size, size), dtype=int)
            for row in range(size):
                for col in range(size):
                    self.board[row, col] = random.randint(0, 1)
        else:
            self.board = np.copy(board)

    def print_board(self, players = []):
        '''
        Print the game board with players and coins.
        Takes an optional list of Player objects to display player positions and scores.
        '''
        empty_cell_symbol = " "
        coin_cell_symbol = "●"
        transparent_coin_symbol = "○"
        
        display_board = np.full((self.size, self.size), empty_cell_symbol, dtype=str)
        for row in range(self.size):
            for col in range(self.size):
                if self.board[row, col] == 1:
                    display_board[row, col] = coin_cell_symbol
                elif self.board[row, col] == 2:
                    display_board[row, col] = transparent_coin_symbol
                    

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
        '''
        Count the number of coins left on the board.
        '''
        return np.sum(self.board != 0)
    
    def nearest_coin_distance(self, start_pos):
        '''
        Find the distance to the nearest coin from a given position using BFS.
        '''
        if self.board[start_pos] == 1:
            return 0
        
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]  # Right, left, down, up
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
        return -float('inf')

    def is_move_valid(self, row, col, players):
        """
        Check if a move is valid: inside the board and not occupied by another player.
        """
        if 0 <= row < self.size and 0 <= col < self.size:
            return not any(player.position == (row, col) for player in players)
        return False

    def transparent_coin(self,supervisor):
        '''
        Every coin has a 50% chance to go transparent and be uncollectable,
        and every transparent coin has a 50% chance to go back to normal
        '''

        for row in range(self.size):
            for col in range(self.size):
                if self.board[row, col] == 1:
                    if random.random() < 0.5:
                        self.board[row, col] = 2
                        supervisor.set_coin_transparency(row=row,column=col, state= self.board[row, col])
                elif self.board[row, col] == 2:
                    if random.random() < 0.5:
                        self.board[row, col] = 1
                        supervisor.set_coin_transparency(row=row,column=col, state= self.board[row, col])

class Player:
    def __init__(self, start_position, score=0):
        self.position = start_position
        self.score = score
        self.consecutive_coins = 0  

    def get_valid_moves(self, board, players):
        """
        Only return moves within the board that do not result in collisions.
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
        self.sim = Sim()
        self.player_index = 0
        self.size = size
        
        print("Initial Board:")
        self.board.print_board()

        for row in range(self.board.size):
            for col in range(self.board.size):
                if self.board.board[row, col] == 1:
                    self.sim.create_coin(row=row,column=col)

    def play_game(self):
        rounds = 0
        for player in self.players:
            if self.board.board[player.position] == 1:
                player.score += 1
                player.consecutive_coins += 1
                self.board.board[player.position] = 0
                row, col = player.position
                self.sim.remove_coin(row=row,column=col)

        move_dict = {(0, 1): 'right', (0, -1): 'left', (1, 0): 'down', (-1, 0): 'up'}
        while self.board.get_coins_left():
            self.board.transparent_coin(self.sim)
            player = self.players[self.player_index]
            best_score, best_move = self.minimax(depth=SEARCH_DEPTH, player_index=self.player_index, is_maximizing=True, alpha=-float('inf'), beta=float('inf'), board=self.board, players=self.players)
            if best_move:
                prev_score = player.score
                self.apply_move(best_move, player)
                row, col = player.position
                self.sim.move_robot(robot_def=f'player{self.player_index+1}',row=row,column=col,direction=move_dict[best_move])
                rounds += 1
                print(f"Round {rounds}: Player {player_dict[self.player_index]} moves {move_dict[best_move]}.", end=" ")
                if player.score > prev_score:
                    print(f"Collected a coin! Total score: {player.score}.", end=" ")
                    if player.consecutive_coins:
                        print(f"({player.consecutive_coins} consecutive coin(s))", end=" ")
                    if (player.score - prev_score) > 1:
                        print(f"Bonus applied! (+{player.score - prev_score - 1})", end=" ")
                print("\nBoard after move:")
                self.board.print_board(self.players)
            self.player_index = 1 - self.player_index 

        self.summarize_game(rounds)

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

    def minimax_move(self, depth=3):
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

        score_diff = player.score - opponent.score

        player_dist = board.nearest_coin_distance(player.position)
        opponent_dist = board.nearest_coin_distance(opponent.position)

        player_advantage = 1 / (player_dist + 0.1)
        opponent_advantage = 1 / (opponent_dist + 0.1)

        proximity_advantage = player_advantage - opponent_advantage

        return score_diff + proximity_advantage

    def simulate_move(self, move, player_index, board, players):
        new_board = GameBoard(board.size, board.board)
        
        new_players = [Player(p.position, p.score) for p in players]
        new_player = new_players[player_index]
        
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
            self.sim.remove_coin(row=new_position[0],column=new_position[1])
            if player.consecutive_coins >= 3:
                bonus = player.consecutive_coins ** 2
                player.score += bonus - player.consecutive_coins
        else:
            player.consecutive_coins = 0

game = Game(size=8)
game.play_game()
