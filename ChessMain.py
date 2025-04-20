import asyncio
import pygame as p
import ChessEngine, ChessAI
import sys
from multiprocessing import Process, Queue
import platform

BOARD_WIDTH = BOARD_HEIGHT = 512
MOVE_LOG_PANEL_WIDTH = 250
MOVE_LOG_PANEL_HEIGHT = BOARD_HEIGHT
DIMENSION = 8
SQUARE_SIZE = BOARD_HEIGHT // DIMENSION
MAX_FPS = 15
IMAGES = {}

# Game modes
MODE_PVP = "Player vs Player"
MODE_PVAI = "Player vs AI"

def loadImages():
    """Load piece, background, and instructions images."""
    pieces = ['wp', 'wR', 'wN', 'wB', 'wK', 'wQ', 'bp', 'bR', 'bN', 'bB', 'bK', 'bQ']
    for piece in pieces:
        IMAGES[piece] = p.transform.scale(p.image.load("images/" + piece + ".png"), (SQUARE_SIZE, SQUARE_SIZE))
    try:
        IMAGES['menu_background'] = p.transform.scale(p.image.load("images/menu.png"), (BOARD_WIDTH + MOVE_LOG_PANEL_WIDTH, BOARD_HEIGHT))
    except FileNotFoundError:
        print("Menu background image not found. Using gradient fallback.")
    try:
        IMAGES['instructions'] = p.image.load("images/HowToPlay.jpg")
    except FileNotFoundError:
        print("Instructions image not found. Please add instructions.png to images/ directory.")

def drawMenu(screen, font, selected_mode):
    """Draw the main menu with a modern, polished design."""
    WHITE = p.Color("white")
    YELLOW = p.Color("yellow")
    GREEN = p.Color("green")
    BLACK = p.Color("black")
    GRAY = p.Color(50, 50, 50)

    def create_gradient_surface(width, height, start_color, end_color):
        surface = p.Surface((width, height))
        for y in range(height):
            t = y / height
            r = int(start_color.r + (end_color.r - start_color.r) * t)
            g = int(start_color.g + (end_color.g - start_color.g) * t)
            b = int(start_color.b + (end_color.b - start_color.b) * t)
            r = max(0, min(255, r))
            g = max(0, min(255, g))
            b = max(0, min(255, b))
            p.draw.line(surface, p.Color(r, g, b), (0, y), (width, y))
        return surface

    # Draw background
    if 'menu_background' in IMAGES:
        screen.blit(IMAGES['menu_background'], (0, 0))
    else:
        gradient = create_gradient_surface(BOARD_WIDTH + MOVE_LOG_PANEL_WIDTH, BOARD_HEIGHT, p.Color(100, 100, 150), p.Color(20, 20, 50))
        screen.blit(gradient, (0, 0))

    # Semi-transparent overlay
    overlay = p.Surface((BOARD_WIDTH + MOVE_LOG_PANEL_WIDTH, BOARD_HEIGHT))
    overlay.set_alpha(50)
    overlay.fill(BLACK)
    screen.blit(overlay, (0, 0))

    # Fonts
    title_font = p.font.SysFont("Georgia", 48, True, False)
    button_font = p.font.SysFont("Arial", 28, True, False)

    # Title
    screen_rect = screen.get_rect()
    title = title_font.render("Chess Game", True, WHITE)
    title_shadow = title_font.render("Chess Game", True, BLACK)
    title_rect = title.get_rect(center=(screen_rect.centerx, screen_rect.height // 6))

    # Buttons
    button_width = 250
    button_height = 50
    button_spacing = 20
    button_y_start = screen_rect.height // 2 - 80

    pvp_text = button_font.render(MODE_PVP, True, YELLOW if selected_mode == MODE_PVP else WHITE)
    pvai_text = button_font.render(MODE_PVAI, True, YELLOW if selected_mode == MODE_PVAI else WHITE)
    instructions_text = button_font.render("How to Play", True, WHITE)
    start_text = button_font.render("Start Game", True, WHITE)

    pvp_rect = p.Rect(0, 0, button_width, button_height)
    pvp_rect.center = (screen_rect.centerx, button_y_start)
    pvai_rect = p.Rect(0, 0, button_width, button_height)
    pvai_rect.center = (screen_rect.centerx, button_y_start + button_height + button_spacing)
    instructions_rect = p.Rect(0, 0, button_width, button_height)
    instructions_rect.center = (screen_rect.centerx, button_y_start + 2 * (button_height + button_spacing))
    start_rect = p.Rect(0, 0, button_width, button_height)
    start_rect.center = (screen_rect.centerx, button_y_start + 3 * (button_height + button_spacing))

    # Hover effects
    mouse_pos = p.mouse.get_pos()
    for rect, text, is_selected in [(pvp_rect, pvp_text, selected_mode == MODE_PVP),
                                    (pvai_rect, pvai_text, selected_mode == MODE_PVAI),
                                    (instructions_rect, instructions_text, False),
                                    (start_rect, start_text, False)]:
        button_color = GRAY if not is_selected else YELLOW.lerp(GRAY, 0.5)
        scale = 1.0
        if rect.collidepoint(mouse_pos):
            button_color = GRAY.lerp(YELLOW, 0.2)
            scale = 1.05

        shadow_rect = rect.copy().move(5, 5)
        p.draw.rect(screen, BLACK, shadow_rect, border_radius=10)
        scaled_rect = rect.copy()
        scaled_rect.width = int(rect.width * scale)
        scaled_rect.height = int(rect.height * scale)
        scaled_rect.center = rect.center
        p.draw.rect(screen, button_color, scaled_rect, border_radius=10)
        p.draw.rect(screen, WHITE, scaled_rect, 2, border_radius=10)
        text_rect = text.get_rect(center=rect.center)
        screen.blit(text, text_rect)

    screen.blit(title_shadow, title_rect.move(3, 3))
    screen.blit(title, title_rect)

    return pvp_rect, pvai_rect, instructions_rect, start_rect

def drawInstructionsScreen(screen, font):
    """Draw the instructions screen with a static image scaled to fit."""
    WHITE = p.Color("white")
    BLACK = p.Color("black")
    GRAY = p.Color(50, 50, 50)
    YELLOW = p.Color("yellow")

    def create_gradient_surface(width, height, start_color, end_color):
        surface = p.Surface((width, height))
        for y in range(height):
            t = y / height
            r = int(start_color.r + (end_color.r - start_color.r) * t)
            g = int(start_color.g + (end_color.g - start_color.g) * t)
            b = int(start_color.b + (end_color.b - start_color.b) * t)
            r = max(0, min(255, r))
            g = max(0, min(255, g))
            b = max(0, min(255, b))
            p.draw.line(surface, p.Color(r, g, b), (0, y), (width, y))
        return surface

    # Draw background
    if 'menu_background' in IMAGES:
        screen.blit(IMAGES['menu_background'], (0, 0))
    else:
        gradient = create_gradient_surface(BOARD_WIDTH + MOVE_LOG_PANEL_WIDTH, BOARD_HEIGHT, p.Color(100, 100, 150), p.Color(20, 20, 50))
        screen.blit(gradient, (0, 0))

    # Semi-transparent overlay
    overlay = p.Surface((BOARD_WIDTH + MOVE_LOG_PANEL_WIDTH, BOARD_HEIGHT))
    overlay.set_alpha(50)
    overlay.fill(BLACK)
    screen.blit(overlay, (0, 0))

    # Fonts
    title_font = p.font.SysFont("Georgia", 48, True, False)
    button_font = p.font.SysFont("Arial", 28, True, False)
    text_font = p.font.SysFont("Arial", 18, False, False)

    # Title
    screen_rect = screen.get_rect()
    title = title_font.render("How to Play", True, WHITE)
    title_shadow = title_font.render("How to Play", True, BLACK)
    title_rect = title.get_rect(center=(screen_rect.centerx, screen_rect.height // 8))

    # Instructions image
    padding = 20
    text_area_width = BOARD_WIDTH + MOVE_LOG_PANEL_WIDTH - 2 * padding
    text_area_height = BOARD_HEIGHT - 200  
    text_area_rect = p.Rect(padding, screen_rect.height // 6 + 20, text_area_width, text_area_height)

    # Render instructions image, scaled to fit
    if 'instructions' in IMAGES:
        instructions_surface = IMAGES['instructions']
        img_width, img_height = instructions_surface.get_size()
        # Calculate scaling to fit within text_area_rect while preserving aspect ratio
        aspect_ratio = img_width / img_height
        target_ratio = text_area_width / text_area_height
        if aspect_ratio > target_ratio:
            # Image is wider relative to target, scale by width
            new_width = text_area_width
            new_height = int(new_width / aspect_ratio)
        else:
            # Image is taller relative to target, scale by height
            new_height = text_area_height
            new_width = int(new_height * aspect_ratio)
        # Scale the image
        scaled_surface = p.transform.scale(instructions_surface, (new_width, new_height))
        # Center the image in text_area_rect
        x = text_area_rect.x + (text_area_width - new_width) // 2
        y = text_area_rect.y + (text_area_height - new_height) // 2
        screen.blit(scaled_surface, (x, y))
    else:
        # Fallback text if image is missing
        fallback_text = text_font.render("Instructions image not found.", True, WHITE)
        screen.blit(fallback_text, (text_area_rect.x + 10, text_area_rect.y + 10))

    # Back button
    button_width = 250
    button_height = 50
    back_text = button_font.render("Back to Menu", True, WHITE)
    back_rect = p.Rect(0, 0, button_width, button_height)
    back_rect.center = (screen_rect.centerx, screen_rect.height - 60)

    # Hover effect
    mouse_pos = p.mouse.get_pos()
    button_color = GRAY
    scale = 1.0
    if back_rect.collidepoint(mouse_pos):
        button_color = GRAY.lerp(YELLOW, 0.2)
        scale = 1.05

    shadow_rect = back_rect.copy().move(5, 5)
    p.draw.rect(screen, BLACK, shadow_rect, border_radius=10)
    scaled_rect = back_rect.copy()
    scaled_rect.width = int(back_rect.width * scale)
    scaled_rect.height = int(back_rect.height * scale)
    scaled_rect.center = back_rect.center
    p.draw.rect(screen, button_color, scaled_rect, border_radius=10)
    p.draw.rect(screen, WHITE, scaled_rect, 2, border_radius=10)
    text_rect = back_text.get_rect(center=back_rect.center)
    screen.blit(back_text, text_rect)

    screen.blit(title_shadow, title_rect.move(3, 3))
    screen.blit(title, title_rect)

    return back_rect

def drawPauseScreen(screen, font):
    """Draw the pause screen with a consistent design."""
    WHITE = p.Color("white")
    YELLOW = p.Color("yellow")
    GREEN = p.Color("green")
    RED = p.Color("red")
    BLACK = p.Color("black")
    GRAY = p.Color(50, 50, 50)

    # Semi-transparent overlay
    overlay = p.Surface((BOARD_WIDTH + MOVE_LOG_PANEL_WIDTH, BOARD_HEIGHT))
    overlay.set_alpha(200)
    overlay.fill(BLACK)
    screen.blit(overlay, (0, 0))

    # Fonts
    title_font = p.font.SysFont("Georgia", 48, True, False)
    button_font = p.font.SysFont("Arial", 28, True, False)

    # Title
    screen_rect = screen.get_rect()
    pause_text = title_font.render("Game Paused", True, WHITE)
    pause_shadow = title_font.render("Game Paused", True, BLACK)
    pause_rect = pause_text.get_rect(center=(screen_rect.centerx, screen_rect.height // 5))

    # Buttons
    button_width = 250
    button_height = 50
    button_spacing = 20
    button_y_start = screen_rect.height // 2 - 100

    resume_text = button_font.render("Resume", True, GREEN)
    menu_text = button_font.render("Back to Menu", True, YELLOW)
    restart_text = button_font.render("Restart", True, RED)

    resume_rect = p.Rect(0, 0, button_width, button_height)
    resume_rect.center = (screen_rect.centerx, button_y_start)
    restart_rect = p.Rect(0, 0, button_width, button_height)
    restart_rect.center = (screen_rect.centerx, button_y_start + button_height + button_spacing)
    menu_rect = p.Rect(0, 0, button_width, button_height)
    menu_rect.center = (screen_rect.centerx, button_y_start + 2 * (button_height + button_spacing))

    # Hover effects
    mouse_pos = p.mouse.get_pos()
    for rect, text in [(resume_rect, resume_text), (menu_rect, menu_text), (restart_rect, restart_text)]:
        button_color = GRAY
        scale = 1.0
        if rect.collidepoint(mouse_pos):
            button_color = GRAY.lerp(YELLOW, 0.2)
            scale = 1.05

        shadow_rect = rect.copy().move(5, 5)
        p.draw.rect(screen, BLACK, shadow_rect, border_radius=10)
        scaled_rect = rect.copy()
        scaled_rect.width = int(rect.width * scale)
        scaled_rect.height = int(rect.height * scale)
        scaled_rect.center = rect.center
        p.draw.rect(screen, button_color, scaled_rect, border_radius=10)
        p.draw.rect(screen, WHITE, scaled_rect, 2, border_radius=10)
        text_rect = text.get_rect(center=rect.center)
        screen.blit(text, text_rect)

    screen.blit(pause_shadow, pause_rect.move(3, 3))
    screen.blit(pause_text, pause_rect)

    return resume_rect, menu_rect, restart_rect

async def main():
    """Main game loop."""
    p.init()
    screen = p.display.set_mode((BOARD_WIDTH + MOVE_LOG_PANEL_WIDTH, BOARD_HEIGHT))
    clock = p.time.Clock()
    font = p.font.SysFont("Arial", 28, True, False)
    move_log_font = p.font.SysFont("Arial", 14, False, False)
    loadImages()

    # Game state variables
    in_menu = True
    in_instructions = False
    in_pause = False
    selected_mode = MODE_PVP
    game_state = None
    valid_moves = []
    move_made = False
    animate = False
    square_selected = ""
    player_clicks = []
    game_over = False
    ai_thinking = False
    move_undone = False
    move_finder_process = None
    player_one = True
    player_two = False
    white_time = 600  # 10 minutes in seconds
    black_time = 600
    last_time_update = p.time.get_ticks()
    end_game_message = ""

    while True:
        if in_menu:
            pvp_rect, pvai_rect, instructions_rect, start_rect = drawMenu(screen, font, selected_mode)
            for e in p.event.get():
                if e.type == p.QUIT:
                    p.quit()
                    sys.exit()
                elif e.type == p.MOUSEBUTTONDOWN:
                    pos = p.mouse.get_pos()
                    if pvp_rect.collidepoint(pos):
                        selected_mode = MODE_PVP
                    elif pvai_rect.collidepoint(pos):
                        selected_mode = MODE_PVAI
                    elif instructions_rect.collidepoint(pos):
                        in_menu = False
                        in_instructions = True
                    elif start_rect.collidepoint(pos):
                        in_menu = False
                        game_state = ChessEngine.GameState()
                        valid_moves = game_state.getValidMoves()
                        player_one = True
                        player_two = selected_mode == MODE_PVP
                        white_time = 600
                        black_time = 600
                        last_time_update = p.time.get_ticks()
            p.display.flip()
            clock.tick(MAX_FPS)
            await asyncio.sleep(1.0 / MAX_FPS)
            continue

        if in_instructions:
            back_rect = drawInstructionsScreen(screen, font)
            for e in p.event.get():
                if e.type == p.QUIT:
                    p.quit()
                    sys.exit()
                elif e.type == p.MOUSEBUTTONDOWN:
                    pos = p.mouse.get_pos()
                    if back_rect.collidepoint(pos):
                        in_instructions = False
                        in_menu = True
                elif e.type == p.KEYDOWN:
                    if e.key == p.K_ESCAPE:
                        in_instructions = False
                        in_menu = True
            p.display.flip()
            clock.tick(MAX_FPS)
            await asyncio.sleep(1.0 / MAX_FPS)
            continue

        if in_pause:
            resume_rect, menu_rect, restart_rect = drawPauseScreen(screen, font)
            for e in p.event.get():
                if e.type == p.QUIT:
                    p.quit()
                    sys.exit()
                elif e.type == p.MOUSEBUTTONDOWN:
                    pos = p.mouse.get_pos()
                    if resume_rect.collidepoint(pos):
                        in_pause = False
                        last_time_update = p.time.get_ticks()
                    elif menu_rect.collidepoint(pos):
                        in_pause = False
                        in_menu = True
                        game_state = ChessEngine.GameState()
                        valid_moves = game_state.getValidMoves()
                        square_selected = ""
                        player_clicks = []
                        move_made = False
                        animate = False
                        game_over = False
                        end_game_message = ""
                        white_time = 600
                        black_time = 600
                        if ai_thinking:
                            move_finder_process.terminate()
                            ai_thinking = False
                    elif restart_rect.collidepoint(pos):
                        game_state = ChessEngine.GameState()
                        valid_moves = game_state.getValidMoves()
                        square_selected = ""
                        player_clicks = []
                        move_made = False
                        animate = False
                        game_over = False
                        end_game_message = ""
                        white_time = 600
                        black_time = 600
                        if ai_thinking:
                            move_finder_process.terminate()
                            ai_thinking = False
                        in_pause = False
                elif e.type == p.KEYDOWN:
                    if e.key == p.K_p:
                        in_pause = False
                        last_time_update = p.time.get_ticks()
            p.display.flip()
            clock.tick(MAX_FPS)
            await asyncio.sleep(1.0 / MAX_FPS)
            continue

        human_turn = (game_state.white_to_move and player_one) or (not game_state.white_to_move and player_two)

        # Update timer
        if not in_menu and not in_instructions and human_turn and not game_over and not in_pause:
            current_time = p.time.get_ticks()
            elapsed = (current_time - last_time_update) / 1000
            if game_state.white_to_move:
                white_time = max(0, white_time - elapsed)
                if white_time <= 0:
                    game_over = True
                    end_game_message = "Black wins by time"
            else:
                black_time = max(0, black_time - elapsed)
                if black_time <= 0:
                    game_over = True
                    end_game_message = "White wins by time"
            last_time_update = current_time

        for e in p.event.get():
            if e.type == p.QUIT:
                p.quit()
                sys.exit()
            elif e.type == p.MOUSEBUTTONDOWN:
                if not game_over and not in_pause:
                    location = p.mouse.get_pos()
                    col = location[0] // SQUARE_SIZE
                    row = location[1] // SQUARE_SIZE
                    if col >= 8:  # Clicked on move log panel
                        continue
                    if square_selected == (row, col):
                        square_selected = ""
                        player_clicks = []
                    else:
                        square_selected = (row, col)
                        player_clicks.append(square_selected)
                    if len(player_clicks) == 2 and human_turn:
                        move = ChessEngine.Move(player_clicks[0], player_clicks[1], game_state.board)
                        for i in range(len(valid_moves)):
                            if move == valid_moves[i]:
                                game_state.makeMove(valid_moves[i])
                                move_made = True
                                animate = True
                                square_selected = ""
                                player_clicks = []
                        if not move_made:
                            player_clicks = [square_selected]
            elif e.type == p.KEYDOWN:
                if e.key == p.K_z:
                    game_state.undoMove()
                    move_made = True
                    animate = False
                    game_over = False
                    end_game_message = ""
                    if ai_thinking:
                        move_finder_process.terminate()
                        ai_thinking = False
                    move_undone = True
                elif e.key == p.K_p:
                    in_pause = True

        # AI move
        if not game_over and not human_turn and not move_undone and not in_pause:
            if not ai_thinking:
                ai_thinking = True
                return_queue = Queue()
                move_finder_process = Process(target=ChessAI.findBestMove, args=(game_state, valid_moves, return_queue))
                move_finder_process.start()
            if not move_finder_process.is_alive():
                ai_move = return_queue.get()
                if ai_move is None:
                    ai_move = ChessAI.findRandomMove(valid_moves)
                game_state.makeMove(ai_move)
                move_made = True
                animate = True
                ai_thinking = False

        if move_made:
            if animate:
                animateMove(game_state.move_log[-1], screen, game_state.board, clock)
            valid_moves = game_state.getValidMoves()
            move_made = False
            animate = False
            move_undone = False

        drawGameState(screen, game_state, valid_moves, square_selected)
        if not game_over:
            drawMoveLog(screen, game_state, move_log_font)
            drawTimer(screen, font, white_time, black_time, game_state.white_to_move)

        if game_state.checkmate:
            game_over = True
            end_game_message = "Black wins by checkmate" if game_state.white_to_move else "White wins by checkmate"
        elif game_state.stalemate:
            game_over = True
            end_game_message = "Stalemate"

        if game_over and end_game_message:
            drawEndGameText(screen, end_game_message)

        p.display.flip()
        clock.tick(MAX_FPS)
        await asyncio.sleep(1.0 / MAX_FPS)

def drawTimer(screen, font, white_time, black_time, white_to_move):
    """Draw the game timer in the move log panel."""
    WHITE = p.Color("white")
    YELLOW = p.Color("yellow")
    BLACK = p.Color("black")

    timer_rect = p.Rect(BOARD_WIDTH, 0, MOVE_LOG_PANEL_WIDTH, 50)
    s = p.Surface((MOVE_LOG_PANEL_WIDTH, 50))
    s.set_alpha(200)
    s.fill(BLACK)
    screen.blit(s, (BOARD_WIDTH, 0))

    white_mins = int(white_time // 60)
    white_secs = int(white_time % 60)
    black_mins = int(black_time // 60)
    black_secs = int(black_time % 60)

    white_color = YELLOW if white_to_move else WHITE
    black_color = YELLOW if not white_to_move else WHITE

    white_text = font.render(f"W: {white_mins:02d}:{white_secs:02d}", True, white_color)
    black_text = font.render(f"B: {black_mins:02d}:{black_secs:02d}", True, black_color)

    screen.blit(white_text, (BOARD_WIDTH + 10, 10))
    screen.blit(black_text, (BOARD_WIDTH + MOVE_LOG_PANEL_WIDTH - black_text.get_width() - 10, 10))

def drawGameState(screen, game_state, valid_moves, square_selected):
    """Draw the current game state."""
    drawBoard(screen)
    highlightSquares(screen, game_state, valid_moves, square_selected)
    drawPieces(screen, game_state.board)

def drawBoard(screen):
    """Draw the chessboard."""
    colors = [p.Color("white"), p.Color("gray")]
    for row in range(DIMENSION):
        for column in range(DIMENSION):
            color = colors[(row + column) % 2]
            p.draw.rect(screen, color, p.Rect(column * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

def highlightSquares(screen, game_state, valid_moves, square_selected):
    """Highlight selected and valid move squares."""
    if len(game_state.move_log) > 0:
        last_move = game_state.move_log[-1]
        s = p.Surface((SQUARE_SIZE, SQUARE_SIZE))
        s.set_alpha(100)
        s.fill(p.Color('green'))
        screen.blit(s, (last_move.end_col * SQUARE_SIZE, last_move.end_row * SQUARE_SIZE))

    if isinstance(square_selected, tuple) and len(square_selected) == 2:
        row, col = square_selected
        if game_state.board[row][col][0] == ('w' if game_state.white_to_move else 'b'):
            s = p.Surface((SQUARE_SIZE, SQUARE_SIZE))
            s.set_alpha(100)
            s.fill(p.Color('blue'))
            screen.blit(s, (col * SQUARE_SIZE, row * SQUARE_SIZE))
            s.fill(p.Color('yellow'))
            for move in valid_moves:
                if move.start_row == row and move.start_col == col:
                    screen.blit(s, (move.end_col * SQUARE_SIZE, move.end_row * SQUARE_SIZE))

def drawPieces(screen, board):
    """Draw pieces on the board."""
    for row in range(DIMENSION):
        for column in range(DIMENSION):
            piece = board[row][column]
            if piece != "--":
                screen.blit(IMAGES[piece], p.Rect(column * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

def drawMoveLog(screen, game_state, font):
    """Draw the move log in the side panel."""
    move_log_rect = p.Rect(BOARD_WIDTH, 50, MOVE_LOG_PANEL_WIDTH, MOVE_LOG_PANEL_HEIGHT - 50)
    p.draw.rect(screen, p.Color('black'), move_log_rect)
    move_log = game_state.move_log
    move_texts = []
    for i in range(0, len(move_log), 2):
        move_string = f"{i // 2 + 1}. {move_log[i]} "
        if i + 1 < len(move_log):
            move_string += str(move_log[i + 1])
        move_texts.append(move_string)
    padding = 5
    line_spacing = 2
    text_y = padding
    for text in move_texts:
        text_object = font.render(text, True, p.Color('white'))
        text_location = move_log_rect.move(padding, text_y)
        screen.blit(text_object, text_location)
        text_y += text_object.get_height() + line_spacing

def drawEndGameText(screen, text):
    """Draw the end game message."""
    font = p.font.SysFont("Helvetica", 32, True, False)
    text_object = font.render(text, False, p.Color("gray"))
    text_location = p.Rect(0, 0, BOARD_WIDTH, BOARD_HEIGHT).move(BOARD_WIDTH / 2 - text_object.get_width() / 2,
                                                                BOARD_HEIGHT / 2 - text_object.get_height() / 2)
    screen.blit(text_object, text_location)
    text_object = font.render(text, False, p.Color('black'))
    screen.blit(text_object, text_location.move(2, 2))

def animateMove(move, screen, board, clock):
    """Animate a move on the board."""
    colors = [p.Color("white"), p.Color("gray")]
    d_row = move.end_row - move.start_row
    d_col = move.end_col - move.start_col
    frames_per_square = 10
    frame_count = (abs(d_row) + abs(d_col)) * frames_per_square
    for frame in range(frame_count + 1):
        row, col = (move.start_row + d_row * frame / frame_count, move.start_col + d_col * frame / frame_count)
        drawBoard(screen)
        drawPieces(screen, board)
        color = colors[(move.end_row + move.end_col) % 2]
        end_square = p.Rect(move.end_col * SQUARE_SIZE, move.end_row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
        p.draw.rect(screen, color, end_square)
        if move.piece_captured != '--':
            if move.is_enpassant_move:
                enpassant_row = move.end_row + 1 if move.piece_captured[0] == 'b' else move.end_row - 1
                end_square = p.Rect(move.end_col * SQUARE_SIZE, enpassant_row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
            screen.blit(IMAGES[move.piece_captured], end_square)
        screen.blit(IMAGES[move.piece_moved], p.Rect(col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
        p.display.flip()
        clock.tick(60)

if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())