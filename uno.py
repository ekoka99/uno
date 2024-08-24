import random
import os

COLORS = ["Red", "Blue", "Green", "Yellow"]
VALUES = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "Skip", "Reverse", "+2"]
WILD_VALUES = ["Wild", "+4"]


class Card:
    def __init__(self, color, value):
        self.original_color = color
        self.current_color = color if color else "Wild"
        self.value = value

    def __str__(self):
        if self.current_color != "Wild":
            return f"{self.current_color[0]}{self.value}"
        return f"{self.value}"

    def render(self):
        if self.current_color != "Wild":
            color_code = self.current_color[0].upper()
            if self.current_color == "Red":
                shade = "░"
            elif self.current_color == "Blue":
                shade = "▒"
            elif self.current_color == "Green":
                shade = "▓"
            else:  # Yellow
                shade = " "
        else:
            color_code = "✧"
            shade = "✧"
        
        value_display = self.value
        if self.value == "Reverse":
            value_display = "Rev"
        
        return [
            f"┌───────────┐",
            f"│{color_code} {shade}        │",
            f"│{shade}{shade}{shade}        │",
            f"│   {value_display:^5}   │",
            f"│        {shade}{shade}{shade}│",
            f"│        {shade} {color_code}│",
            f"└───────────┘"
        ]

    def copy_with_new_color(self, new_color):
        new_card = Card(new_color, self.value)
        return new_card

    def reset_wild_color(self):
        if self.value in WILD_VALUES:
            self.current_color = "Wild"


class Deck:
    def __init__(self):
        self.cards = []
        for color in COLORS:
            for value in VALUES:
                self.cards.append(Card(color, value))
        for _ in range(4):
            self.cards.append(Card(None, "Wild"))
            self.cards.append(Card(None, "+4"))
        random.shuffle(self.cards)

    def draw(self):
        if not self.cards:
            self.reshuffle_discard_pile()
        if self.cards:
            card = self.cards.pop()
            card.reset_wild_color()
            return card
        else:
            print("No cards left to draw!")
            return None

    def reshuffle_discard_pile(self):
        global discard_pile
        if len(discard_pile) > 1:
            print("Reshuffling the discard pile.")
            top_card = discard_pile.pop()
            self.cards = discard_pile
            for card in self.cards:
                card.reset_wild_color()
            discard_pile = [top_card]
            random.shuffle(self.cards)
        else:
            print("Not enough cards in the discard pile to reshuffle.")


class Player:
    def __init__(self, name, is_ai=False, difficulty="Medium"):
        self.name = name
        self.hand = []
        self.is_ai = is_ai
        self.difficulty = difficulty

    def draw(self, deck, num=1):
        for _ in range(num):
            card = deck.draw()
            if card:
                card.reset_wild_color()
                self.hand.append(card)
        self.sort_hand()

    def play(self, card):
        if card in self.hand:
            self.hand.remove(card)
            return card
        else:
            raise ValueError("Card not in player's hand")

    def sort_hand(self):
        self.hand.sort(
            key=lambda x: (
                x.current_color != "Wild",
                x.current_color,
                VALUES.index(x.value) if x.value in VALUES else len(VALUES),
            )
        )

    def evaluate_game_state(self, players, current_player):
        cards_left = sum(len(player.hand) for player in players)
        game_progress = 1 - (
            cards_left / (len(players) * 7)
        )
        return game_progress


def is_valid_play(card, top_card):
    if card.value in WILD_VALUES:
        return True
    if card.current_color == top_card.current_color or card.value == top_card.value:
        return True
    return False


def choose_color(player, hand):
    if player.is_ai:
        color_counts = {
            color: len([card for card in hand if card.current_color == color])
            for color in COLORS
        }
        return (
            max(color_counts, key=color_counts.get)
            if color_counts
            else random.choice(COLORS)
        )
    while True:
        color = input("Choose a color (Red/Blue/Green/Yellow): ").capitalize()
        if color in COLORS:
            return color
        print("Invalid color. Please try again.")


def ai_play_easy(player, top_card, players, current_player):
    playable_cards = [card for card in player.hand if is_valid_play(card, top_card)]
    if random.random() < 0.5:
        return random.choice(playable_cards) if playable_cards else None
    for card in playable_cards:
        if card.current_color == top_card.current_color or card.value == top_card.value:
            return card
    return playable_cards[0] if playable_cards else None

def ai_play_medium(player, top_card, players, current_player):
    playable_cards = [card for card in player.hand if is_valid_play(card, top_card)]
    game_progress = player.evaluate_game_state(players, current_player)

    if game_progress < 0.5:
        non_wild_cards = [
            card for card in playable_cards if card.current_color != "Wild"
        ]
        if non_wild_cards:
            return random.choice(non_wild_cards)

    if random.random() < 0.25:
        return random.choice(playable_cards) if playable_cards else None
    return ai_play_hard(player, top_card, players, current_player)

def ai_play_hard(player, top_card, players, current_player):
    playable_cards = [card for card in player.hand if is_valid_play(card, top_card)]
    game_progress = player.evaluate_game_state(players, current_player)

    if game_progress < 0.7:
        non_wild_cards = [
            card for card in playable_cards if card.current_color != "Wild"
        ]
        if non_wild_cards:
            action_cards = [
                card
                for card in non_wild_cards
                if card.value in ["Skip", "Reverse", "+2"]
            ]
            color_matches = [
                card for card in non_wild_cards if card.current_color == top_card.current_color
            ]
            if action_cards:
                return max(
                    action_cards, key=lambda c: ["Skip", "Reverse", "+2"].index(c.value)
                )
            elif color_matches:
                return max(color_matches, key=lambda c: VALUES.index(c.value))
            else:
                return max(non_wild_cards, key=lambda c: VALUES.index(c.value))
        elif len(player.hand) > 1:
            return None

    wild_cards = [card for card in playable_cards if card.current_color == "Wild"]
    if wild_cards:
        best_color = max(
            COLORS,
            key=lambda color: len(
                [card for card in player.hand if card.current_color == color]
            ),
        )
        chosen_wild = max(wild_cards, key=lambda c: c.value)
        chosen_wild.set_color(best_color)
        return chosen_wild

    return (
        max(playable_cards, key=lambda c: VALUES.index(c.value))
        if playable_cards
        else None
    )

def ai_play(player, top_card, players, current_player):
    if player.difficulty == "Easy":
        return ai_play_easy(player, top_card, players, current_player)
    elif player.difficulty == "Medium":
        return ai_play_medium(player, top_card, players, current_player)
    else:
        return ai_play_hard(player, top_card, players, current_player)


def render_stacked_cards(num_cards, width):
    if num_cards == 0:
        return " " * width
    if num_cards == 1:
        return "[]".center(width)
    stack = f"[{']' * (num_cards - 1)}]"
    return stack.center(width)


def render_vertical_stack(num_cards):
    if num_cards == 0:
        return ["     "]
    
    stack = ["⎴    "]
    stack.extend(["⎵    "] * num_cards)
    
    return stack


def render_game_state(players, current_player, top_card, direction, debug_mode=False):
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # Calculate the position of the card
    card_left_margin = 35  # Adjust this value to center the card
    
    # Render AI 2's stack
    ai2_stack = render_stacked_cards(len(players[2].hand), 11)  # Reduce width to match card width
    print(f"{players[2].name:^80}")
    print(f"{' ' * card_left_margin}{ai2_stack}")
    print()
    
    top_card_render = top_card.render()
    ai1_stack = render_vertical_stack(len(players[1].hand))
    ai3_stack = render_vertical_stack(len(players[3].hand))
    
    max_height = max(len(ai1_stack), len(ai3_stack), len(top_card_render))
    
    ai1_stack += ["     "] * (max_height - len(ai1_stack))
    ai3_stack += ["     "] * (max_height - len(ai3_stack))
    top_card_render += ["           "] * (max_height - len(top_card_render))
    
    # Direction indicators
    top_arrow = "→" if direction == 1 else "←"
    side_arrow_left = "↑" if direction == 1 else "↓"
    side_arrow_right = "↓" if direction == 1 else "↑"
    bottom_arrow = "←" if direction == 1 else "→"

    # Render AI hands and top card with direction indicators
    print(f"{' ' * card_left_margin}{top_arrow:^11}")  # Top arrow centered above the card
    for i in range(max_height):
        if i == 3:  # Assuming the card value is on the 4th line (index 3)
            print(f"{ai1_stack[i]:<5}{' ' * (card_left_margin - 5)}{side_arrow_left} {top_card_render[i]} {side_arrow_right}{' ' * (74 - card_left_margin - len(top_card_render[i]))}{ai3_stack[i]}")
        else:
            print(f"{ai1_stack[i]:<5}{' ' * (card_left_margin - 5)}  {top_card_render[i]}  {' ' * (74 - card_left_margin - len(top_card_render[i]))}{ai3_stack[i]}")
    print(f"{' ' * card_left_margin}{bottom_arrow:^11}")  # Bottom arrow centered below the card

    print(f"{players[1].name:<20}{' ' * 40}{players[3].name:>20}")
    print()
    
    print(f"{players[0].name:^80}")
    print("Your hand:")
    hand_render = [card.render() for card in players[0].hand]
    for i in range(7):
        print("".join(card[i] for card in hand_render))
    
    print(f"\nCurrent player: {players[current_player].name}")

    if debug_mode:
        print("\nDEBUG INFO:")
        for i, player in enumerate(players):
            if i != 0:
                print(f"{player.name}: {', '.join(str(card) for card in player.hand)}")
        print(f"Cards left in deck: {len(deck.cards)}")
        if deck.cards:
            print(f"Top card of deck: {deck.cards[-1]}")
        print("\nPress Enter to continue...")
        input()

deck = Deck()
discard_pile = [deck.draw()]
while discard_pile[0].value in WILD_VALUES:
    deck.cards.append(discard_pile.pop())
    random.shuffle(deck.cards)
    discard_pile = [deck.draw()]

difficulties = ["Easy", "Medium", "Hard"]

players = [
    Player("You"),
    Player(f"AI 1 ({random.choice(difficulties)})", True, random.choice(difficulties)),
    Player(f"AI 2 ({random.choice(difficulties)})", True, random.choice(difficulties)),
    Player(f"AI 3 ({random.choice(difficulties)})", True, random.choice(difficulties)),
]

for player in players:
    player.draw(deck, 7)
    player.sort_hand()

current_player = random.randint(0, 3)
direction = 1

print(f"{players[current_player].name} will start the game!")
input("Press Enter to begin...")

#core game loop
debug_mode = False
while True:
    player = players[current_player]
    top_card = discard_pile[-1]
    
    render_game_state(players, current_player, top_card, direction, debug_mode)
    
    if player.is_ai:
        card = ai_play(player, top_card, players, current_player)
        if card:
            player.play(card)
            print(f"{player.name} played {card}")
        else:
            drawn_card = deck.draw()
            if drawn_card:
                player.hand.append(drawn_card)
                player.sort_hand()
                print(f"{player.name} draws a card.")
                if is_valid_play(drawn_card, top_card):
                    print(f"{player.name} plays the drawn card: {drawn_card}")
                    player.play(drawn_card)
                    card = drawn_card
                else:
                    print(f"{player.name} cannot play the drawn card.")
            else:
                print(f"No cards left for {player.name} to draw.")
    else:
        valid_play = False
        while not valid_play:
            choice = input("Choose a card to play (number), 'd' to draw, or 'debug' to toggle debug mode: ").lower()
            if choice == 'debug':
                debug_mode = not debug_mode
                print(f"Debug mode {'enabled' if debug_mode else 'disabled'}")
                render_game_state(players, current_player, top_card, direction, debug_mode)
                continue
            elif choice == 'd':
                drawn_card = deck.draw()
                if drawn_card:
                    player.hand.append(drawn_card)
                    player.sort_hand()
                    print(f"You drew: {drawn_card}")
                    if is_valid_play(drawn_card, top_card):
                        play = input("Do you want to play this card? (y/n): ")
                        if play.lower() == 'y':
                            player.play(drawn_card)
                            card = drawn_card
                            valid_play = True
                            print(f"You played {card}")
                        else:
                            print("You chose not to play the drawn card.")
                    else:
                        print("This card cannot be played.")
                else:
                    print("No cards left to draw.")
                if not valid_play:
                    break
            else:
                try:
                    index = int(choice) - 1
                    card = player.hand[index]
                    if is_valid_play(card, top_card):
                        player.play(card)
                        print(f"You played {card}")
                        valid_play = True
                    else:
                        print("Invalid play. Try again.")
                except (ValueError, IndexError):
                    print("Invalid input. Try again.")
    
    if 'card' in locals() and card:
        if card.value in WILD_VALUES:
            new_color = choose_color(player, player.hand)
            print(f"{player.name} changes the color to {new_color}")
            card = card.copy_with_new_color(new_color)
        discard_pile.append(card)
        
        if len(player.hand) == 1:
            if player.is_ai:
                print(f"{player.name} calls UNO!")
            else:
                uno_call = input("Do you want to call UNO? (y/n): ")
                if uno_call.lower() != 'y':
                    print(f"{player.name} forgot to call UNO! Drawing 2 cards as penalty.")
                    player.draw(deck, 2)
                    player.sort_hand()
        
        if len(player.hand) == 0:
            render_game_state(players, current_player, card, debug_mode)
            print(f"{player.name} wins!")
            break
        
        if card.value == "Reverse":
            direction *= -1
            print("Direction reversed!")
            next_player = (current_player + direction) % len(players)
        elif card.value == "Skip":
            next_player = (current_player + 1 * direction) % len(players)
            print(f"{players[next_player].name} is skipped!")
        elif card.value == "+2":
            next_player = (current_player + direction) % len(players)
            players[next_player].draw(deck, 2)
            players[next_player].sort_hand()
            print(f"{players[next_player].name} draws 2 cards and is skipped!")
            next_player = (next_player + direction) % len(players)
        elif card.value == "+4":
            next_player = (current_player + direction) % len(players)
            players[next_player].draw(deck, 4)
            players[next_player].sort_hand()
            print(f"{players[next_player].name} draws 4 cards and is skipped!")
            next_player = (next_player + direction) % len(players)
        else:
            next_player = (current_player + direction) % len(players)
    else:
        next_player = (current_player + direction) % len(players)
    
    current_player = next_player
    if not debug_mode:
        input("Press Enter to continue...")
