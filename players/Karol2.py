from typing import List, Dict, Any
from collections import Counter
from bot_api import PokerBotAPI, PlayerAction, GameInfoAPI
from engine.cards import Card, Rank
from engine.poker_game import GameState

class Karol2Bot(PokerBotAPI):
    def __init__(self, name: str):
        super().__init__(name)
        self.hands_played = 0
        self.hands_won = 0

        self.premium_hands = [
            (Rank.ACE, Rank.ACE), (Rank.KING, Rank.KING),(Rank.QUEEN, Rank.QUEEN),
            (Rank.JACK, Rank.JACK),(Rank.TEN, Rank.TEN), (Rank.ACE, Rank.KING), 
            (Rank.ACE, Rank.QUEEN), (Rank.ACE, Rank.JACK), (Rank.KING, Rank.QUEEN),
            (Rank.KING, Rank.JACK), (Rank.QUEEN, Rank.JACK)
        ]

    # ---------- HAND EVALUATION ----------

    def evaluate_hand_strength(self, cards: List[Card]) -> str:
        ranks = [c.rank.value for c in cards]
        suits = [c.suit for c in cards]

        rank_counts = Counter(ranks)
        suit_counts = Counter(suits)

        is_flush = max(suit_counts.values()) >= 5
        sorted_ranks = sorted(set(ranks))

        # Straight detection (Ace low included)
        is_straight = False
        for i in range(len(sorted_ranks) - 4):
            if sorted_ranks[i + 4] - sorted_ranks[i] == 4:
                is_straight = True

        counts = sorted(rank_counts.values(), reverse=True)

        if is_flush and is_straight:
            return "STRAIGHT_FLUSH"
        if counts.count(4)>= 1:
            return "FOUR_OF_A_KIND"
        if 3 in counts and 2 in counts:
            return "FULL_HOUSE"
        if is_flush:
            return "FLUSH"
        if is_straight:
            return "STRAIGHT"
        if counts.count(3)>= 1:
            return "THREE_OF_A_KIND"
        if counts.count(2) >= 2:
            return "TWO_PAIR"
        if counts.count(2) >= 1:
            pair_rank = max(rank for rank, count in rank_counts.items() if count == 2)
            if pair_rank <= 6:
                return "LOW_PAIR"
            if pair_rank <= 10:
                return "MID_PAIR"
            else:
                return "HIGH_PAIR"
        return "WEAK"

    # ---------- MAIN DECISION ----------

    def get_action(
        self,
        game_state: GameState,
        hole_cards: List[Card],
        legal_actions: List[PlayerAction],
        min_bet: int,
        max_bet: int
    ) -> tuple:

        if len(hole_cards) != 2:
            return PlayerAction.FOLD, 0

        card1, card2 = hole_cards

        hand1 = (card1.rank, card2.rank)
        hand2 = (card2.rank, card1.rank)

        is_premium = hand1 in self.premium_hands or hand2 in self.premium_hands

        if (is_premium):
            if PlayerAction.RAISE in legal_actions:
                raise_amount = min(game_state.current_bet + game_state.pot // 2, max_bet)
                raise_amount = max(raise_amount, min_bet)
                return PlayerAction.RAISE, raise_amount

        #--------- POST-FLOP LOGIC ----
        community = getattr(game_state, "community_cards", [])

        if len(community) == 3:
            all_cards = hole_cards + community
            hand_strength = self.evaluate_hand_strength(all_cards)

            to_call = GameInfoAPI.calculate_bet_amount(
                game_state.current_bet,
                game_state.player_bets[self.name]
            )
            
            if hand_strength in ("STRAIGHT_FLUSH", "FOUR_OF_A_KIND", "FULL_HOUSE", "FLUSH", "STRAIGHT", "THREE_OF_A_KIND", "TWO_PAIR", "HIGH_PAIR", "MID_PAIR"):
                return PlayerAction.RAISE, min(game_state.pot, max_bet)

            if hand_strength in ("LOW_PAIR"):
                if to_call <= game_state.pot * 0.3:
                    return PlayerAction.CALL, 0
                return PlayerAction.FOLD, 0
        # -------- TURN LOGIC ---------

        if len(community) == 4:
            hand_strength = self.evaluate_hand_strength(all_cards)

            to_call = GameInfoAPI.calculate_bet_amount(
                game_state.current_bet,
                game_state.player_bets[self.name]
            )
            
            if hand_strength in ("STRAIGHT_FLUSH", "FOUR_OF_A_KIND", "FULL_HOUSE", "FLUSH", "STRAIGHT", "THREE_OF_A_KIND"):
                return PlayerAction.RAISE, min(game_state.pot, max_bet)

            if hand_strength in ("TWO_PAIR", "HIGH_PAIR", "MID_PAIR"):
                if to_call <= game_state.pot * 0.3:
                    return PlayerAction.CALL, 0
                return PlayerAction.FOLD, 0
        # -------- RIVER LOGIC --------

        if len(community) == 5:
            hand_strength = self.evaluate_hand_strength(all_cards)

            to_call = GameInfoAPI.calculate_bet_amount(
                game_state.current_bet,
                game_state.player_bets[self.name]
            )
            
            if hand_strength in ("STRAIGHT_FLUSH", "FOUR_OF_A_KIND", "FULL_HOUSE", "FLUSH", "STRAIGHT"):
                return PlayerAction.RAISE, min(game_state.pot, max_bet)

            if hand_strength in ("THREE_OF_A_KIND", "TWO_PAIR", "HIGH_PAIR"):
                if to_call <= game_state.pot * 0.3:
                    return PlayerAction.CALL, 0
                return PlayerAction.FOLD, 0

        if PlayerAction.CHECK in legal_actions:
            return PlayerAction.CHECK, 0
        return PlayerAction.FOLD, 0

    # ---------- HAND COMPLETE ----------

    def hand_complete(self, game_state: GameState, hand_result: Dict[str, Any]):
        self.hands_played += 1

        if "winners" in hand_result and self.name in hand_result["winners"]:
            self.hands_won += 1

        if self.hands_played % 25 == 0:
            win_rate = self.hands_won / self.hands_played
            self.logger.info(
                f"Conservative play: {self.hands_won}/{self.hands_played} "
                f"wins ({win_rate:.2%})"
            )