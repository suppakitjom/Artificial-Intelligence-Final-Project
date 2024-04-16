from controller import Supervisor
import random
x_offset = 0.35
y_offset = -0.35


def create_coin(supervisor, i, j):
    x,y = get_x_y(i,j)
    global coin_count
    # Create a unique name for each coin
    coin_name = f"coin_{i}_{j}"
    
    # Adjust the coin position and name for a different orientation or logic
    coin_def_string = f'Coin {{ translation {x} {y} 0.025 name "{coin_name}" }}'
    root_node = supervisor.getRoot()
    children_field = root_node.getField('children')
    children_field.importMFNodeFromString(-1, coin_def_string)

def main():
    supervisor = Supervisor()
    timestep = int(supervisor.getBasicTimeStep())

    global arena
    arena = supervisor.getFromDef('arena')
    if arena is None:
        print("Arena node not found!")
        return
    global floor_size
    floor_size = arena.getField('floorSize').getSFVec2f()

    for i in range(0, 10):
        for j in range(0, 10):
            if random.randint(0, 1) == 1:
                create_coin(supervisor, i, j)
            supervisor.step(timestep)

def get_x_y(i,j):
    tile_size = 0.1  # Assuming each tile is 0.1 meters for this example
    center_x = -floor_size[0] / 2 + x_offset
    center_y = -floor_size[1] / 2 + y_offset
    x = center_x + (j + 0.5) * tile_size
    y = center_y + (i + 0.5) * tile_size
    return x,y

if __name__ == "__main__":
    main()




