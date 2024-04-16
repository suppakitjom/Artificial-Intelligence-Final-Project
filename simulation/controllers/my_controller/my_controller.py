import numpy as np
import random
from collections import deque
import math
from controller import Supervisor

# random.seed(0)
player_dict = {0:'X', 1:'Y'}

class Sim(Supervisor):
    def __init__(self):
        self.game = Supervisor()
        self.timestep = int(self.game.getBasicTimeStep())
        self.arena = self.game.getFromDef('arena')

    def get_x_y(self,row,column):
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
        x, y = self.get_x_y(row=row,column=column)
        coin_def = f"coin_{row}_{column}"
        coin_def_string = f'DEF {coin_def} Coin {{ translation {x} {y} 0.025 name "{coin_def}" }}'
        root_node = self.game.getRoot()
        children_field = root_node.getField('children')
        children_field.importMFNodeFromString(-1, coin_def_string)

    def remove_coin(self,row,column):
        coin_name = f"coin_{row}_{column}"
        print(f"Removing coin {coin_name}")
        coin_node = self.game.getFromDef(coin_name)
        coin_node.remove()

    def move_robot(self,robot_def,row,column,direction):
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
        self.sim = Sim()
        self.rounds = 0
        print("Initial Board:")
        self.board.print_board()

        for row in range(self.board.size):
            for col in range(self.board.size):
                if self.board.board[row, col] == 1:
                    self.sim.create_coin(row=row,column=col)
    

    
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
                self.sim.remove_coin(row=row,column=col)

        print("Game Start!")
        self.board.print_board(self.players)

        player_index = 0

        while self.board.get_coins_left():  # Continue until all coins are collected
            player = self.players[player_index]
            selected_move = player.move(self.board, self.players)

            row, col = player.position
            self.sim.move_robot(robot_def=f"player{player_index+1}",row=row,column=col,direction=move_dict[selected_move])
            if self.board.board[row, col] == 1:
                player.score += 1
                player.consecutive_coins += 1
                self.board.board[row, col] = 0
                self.sim.remove_coin(row=row,column=col)

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
            self.sim.game.step(self.sim.timestep)

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