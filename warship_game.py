# stdlib
import os
import sys
import logging as log
import itertools as it

from time import sleep
from functools import reduce
from random import randint

log.basicConfig(level=log.DEBUG)

TURNS = 35
SHIPS_LEN = {"A": 5, "B": 4, "S": 3, "D": 3, "P": 2}


def generate_board(dim: int = 10, filler: str = "~") -> [[str]]:
    """Generate a new board object"""
    return [[filler] * dim for _ in range(dim)]


def place_ship(
    row: int,
    col: int,
    board: [[str]],
    ship: str,
    orientation: str = "v",
    filler: str = "~",
) -> (bool, [[str]]):
    """
    Place the ship into a required location.

    It checks if the possible entries are within bounds and if they aren't already
    occupied.

    If it fails it will return the original board

    Note:
    -----
    This function alters the original board. So if you have a list make sure you are aware that
    the underlying data of the list will be changed.

    Parameters:
    -----------
    row: int
    col: int
    board: [[str]]
    ship: str
    orientation: str

    Returns:
    --------
    (bool, board)
        a tuple incidating success of placement and the reference to the board
    """
    ship_len = SHIPS_LEN[ship]

    valid = validate_bounds(board, row, col, ship_len, orientation)

    fallback = (False, board.copy())
    if not valid:
        return fallback

    if orientation == "v":
        for i in range(ship_len):
            board[row + i][col] = ship
        return (True, board)

    elif orientation == "h":
        for i in range(ship_len):
            board[row][col + i] = ship
        return (True, board)
    else:
        raise ValueError("Incorrect orientation provided")


def validate_bounds(
    board: [[str]], row: int, col: int, ship_len: int, orientation: str, filler="~"
) -> bool:
    """Validate bounds.

    Currently this takes a ship length and the position that the player wants to put it into.

    It also check the orientation. Because I realised that if I check the length + row and length + col
    at all times, then it will fail when you're trying to put stuff at the very end of the board
    horizontally.

    """
    "TODO: make sure this adds up with the right length "

    if orientation == "v" and ((row + ship_len) < 10):
        for i in range(ship_len):
            if board[row + i][col] != filler:
                log.debug(
                    f"Could not place ship vertically. Coordinate {(col, row+i)} is already occupied"
                )
                return False

    elif orientation == "h" and ((col + ship_len) < 10):
        for i in range(ship_len):
            if board[row][col + i] != filler:
                log.debug(
                    f"Could not place ship horizontally. Coordinate {(col+i, row)} is already occupied"
                )
                return False

    elif orientation not in ["h", "v"]:
        log.debug(f"Could not place ship of length {ship_len} in position {(row, col)}")
        return False

    # NOTE: this is annoying that i have to repeat myself. Might need to abstract the predicates
    # TODO: refactor all these conditionals but for now it works.
    elif (row + ship_len) >= 10 or (col + ship_len) >= 10:
        return False

    return True


def populate_board(board: [[str]], ships: [str] = list(SHIPS_LEN.keys())) -> [[str]]:
    """Populate board with a selection of ships"""
    # TODO: populate docstring
    for ship in ships:

        placed = False
        while not placed:
            row, col = randint(0, 9), randint(0, 9)
            orientation = randint(0, 1)
            placed, board = place_ship(
                row, col, board, ship, {1: "v", 0: "h"}[orientation]
            )

    return board


def get_state(board: [[str]], filler="~") -> [(str, int, int)]:
    """Dump the state of the board into an array of tuples"""
    state = []
    for ri, row in enumerate(board):
        for ci, col in enumerate(row):
            if col != "~":
                state.append((col, ri, ci))

    return state


def set_state(board: [[str]], state: [(str, int, int)]) -> [(str, int, int)]:
    """Take in a state in the required format and load it into the board"""
    for ship, ri, ci in state:
        board[ri][ci] = ship
    return board


def io_print_sleep(text: str, s: int) -> None:
    """Print the value and and wait.

    The function adds `: 3s`, `: 2s` ... etc.
    """
    for i in range(s, 0, -1):

        sys.stdout.write(f"\r{text} ({i}s)")
        sys.stdout.flush()  # important
        sleep(1)


def io_validate_input(val, valid=list(map(str, range(10)))):
    """Sanitize imputs

    Returns a boolean representing the validity and the value

    Returns
    -------
    (bool, a)

    """
    return (True, val) if val in valid else (False, val)


def io_save_board(board: [[str]], filename: str = "checkpoint.sav") -> bool:
    """Save the state of the board to file

    It will be saved in the format `(ship, row_index, column_index)`
    Avoids us storing null's
    """
    with open(filename, "w+") as handle:
        handle.writelines(map(lambda row: str(row) + "\n", get_state(board)))

    return True


def io_load_board(filename: str = "checkpoint.sav", custom_filler="~") -> [[str]]:
    """Load the state of the board from file

    Loads in a file exported by `io_save_board` and shoves it into a new board
    """
    board: [[str]] = generate_board(filler=custom_filler)
    with open(filename, "r") as handle:
        state = handle.read().splitlines()

    full_board = set_state(board, [eval(e) for e in state])

    return full_board


def io_render_main_menu(main_menu_file: str = "main_menu", radar=False) -> bool:
    """Load the main menu from file and print it to the screen"""
    with open(main_menu_file, "r") as handle:
        menu = handle.read()

    radar = "on" if radar else "off"
    print(menu.format(radar))

    return True


def io_render_board(board: [[str]], sep=" | ") -> None:
    """Renders the board"""

    def _format(s1, s2):
        return s1 + sep + s2

    l = len(reduce(_format, board[0]))
    dash = lambda: print("   ", "-" * (l + 2))

    print("     0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 ")

    for i, row in enumerate(board):
        dash()
        print(f"{i}.  ", reduce(_format, row))

    dash()


def io_main_menu(feedback="", radar=False) -> None:
    """Main menu logic. Asks for user input and kicks off game loop"""
    selecting = True
    cheats = False

    while selecting:
        io_clear_screen()
        io_render_main_menu(radar=radar)

        feedback_line = ">> " + feedback + "\n"

        # TODO: add niceformatting
        # pad = 80 - len(feedback_line) - 4
        # feedback_line += (" " * pad) + "<<"

        print(feedback_line)

        choice = input("Choose (n/c/q): ")

        if choice == "uuddlrlrab":
            cheats = True
            feedback = "Cheats Enabled >:)"
            continue

        if choice == "radar":
            radar = not radar
            continue

        if choice not in ["n", "c", "q"]:

            feedback = f"Incorrect choice ({choice})."
            continue

        else:
            break

    if choice == "n":
        board = populate_board(generate_board())
        game_loop(board, cheats, radar)

    elif choice == "c":
        board = io_load_board("checkpoint.sav")
        game_loop(board, cheats, radar)

    elif choice == "q":
        sys.exit()


def io_clear_save() -> bool:
    """Clear save file

    TODO: do something wherever the boolean comes back
    """
    try:
        os.remove("checkpoint.sav")
        return True
    except Exception as e:
        log.debug(f"Got error in clearing save: {e}")
        return False


def io_win_screen():
    """Handles rendering of the win screen"""
    io_clear_screen()
    with open("win_screen", "r") as handle:
        print(handle.read())
    input("Press enter to continue")
    io_main_menu("Nice one, let's go again?")


def io_clear_screen() -> None:
    """Clears the screen in the terminal"""
    # TODO: replace with something more robust
    print(chr(27) + "[2J")  # clears screen


def get_turn(board: [[str]], only: [[str]] = ["@", "X"]) -> None:
    unfolded = [entry for row in board for entry in row]
    return (
        sum(filter(lambda i: i, map(lambda e: e in only, unfolded))) + 1
    )  # add one as it starts from 0


def mask_board(board: [[str]], extra: [str] = ["@", "X"], filler: str = "~") -> [[str]]:
    """Mask certain elements from the board with the filler character

    Useful when we show the user the board
    """
    return [
        [component if component in ([filler] + extra) else filler for component in row]
        for row in board
    ]


def game_loop(board: [[str]], cheats: bool, radar, filler: str = "~", turns=20) -> None:
    """Main game loop with user input and rendering"""

    def _save_main_menu(inp: str) -> None:
        if inp == "m":
            io_save_board(board)
            io_main_menu("Game saved", radar=radar)

    if win_condition(board):
        io_clear_save()
        io_win_screen()

    turn = get_turn(board)
    if turn == turns:
        io_clear_save()
        io_main_menu("You ran out of ammo, try again", radar=radar)

    io_clear_screen()
    print("Input `m` to save and go to the main menu")
    print(f"Turn: {turn}/{turns}\n")

    user_board = mask_board(board)
    io_render_board(user_board)

    if cheats:
        print("-" * 80)
        io_render_board(board)

    _validr, _r = io_validate_input(input("Please enter a row: "))
    _save_main_menu(_r)  # save and exit to main menu if choice == "m"

    _validc, _c = io_validate_input(input("Please enter a col: "))
    _save_main_menu(_c)  # save and exit to main menu if choice == "m"

    if _validr and _validc:
        r: int = int(_r)
        c: int = int(_c)
    else:
        io_print_sleep("Sorry, incorrect input", s=2)
        game_loop(board, cheats, radar)

    hit_miss: str = board[r][c]

    # TODO: need to ensure that if i already guessed here, we keep going

    if (hit_miss == "@") or (hit_miss == "X"):
        io_print_sleep("You have already targeted this area", s=2)
        game_loop(board, cheats, radar)

    elif (hit_miss != filler) and (hit_miss != "@"):
        board[r][c] = "X"

        if radar and radar_scan(board, r, c):
            io_print_sleep("Enemy nearby!", 2)

        game_loop(board, cheats, radar)

    elif hit_miss == filler:
        board[r][c] = "@"

        if radar and radar_scan(board, r, c):
            io_print_sleep("Enemy nearby!", 2)

        game_loop(board, cheats, radar)

    else:
        game_loop(board, cheats, radar)


def radar_scan(board: [[str]], r: int, c: int, ignore=["@", "X", "~"]) -> None:
    """Check if any entries one block away from the guess have ships"""
    valid = (
        lambda t: (r + t[0] < 10)
        and (c + t[0] > -1)
        and (r + t[1] < 10)
        and (c + t[1] > -1)
    )
    entries = filter(valid, it.product(range(-1, 2), range(-1, 2)))
    check = lambda t: board[r + t[0]][c + t[1]] not in ignore
    aa = map(check, entries)
    return any(aa)


def win_condition(board: [[str]], ignore=["X", "@", "~"]) -> None:
    """Check if the board contains entries that aren't the miss, filler or hit"""
    unfolded = [entry for row in board for entry in row]
    return all(map(lambda entry: entry in ignore, unfolded))


if __name__ == "__main__":
    io_main_menu()
