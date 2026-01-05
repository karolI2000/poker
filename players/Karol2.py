"""
Conservative Bot - Plays very tight and safe
Only plays strong hands and folds most of the time
"""
from typing import List, Dict, Any

from bot_api import PokerBotAPI, PlayerAction, GameInfoAPI
from engine.cards import Card, Rank
from engine.poker_game import GameState


class ConservativeBot(PokerBotAPI):
    """
    A conservative bot that only plays very strong hands.
    Good example of a tight playing style.
    """
    
    def __init__(self, name: str):
        super().__init__(name)
        self.hands_played = 0
        self.hands_won = 0
        
        # Define strong starting hands
        self.premium_hands = [
            (Rank.ACE, Rank.ACE), (Rank.KING, Rank.KING), (Rank.QUEEN, Rank.QUEEN),
            (Rank.JACK, Rank.JACK), (Rank.TEN, Rank.TEN), (Rank.NINE, Rank.NINE),
            (Rank.EIGHT, Rank.EIGHT),(Rank.SEVEN, Rank.SEVEN),(Rank.ACE, Rank.KING),
            (Rank.ACE, Rank.QUEEN), (Rank.ACE, Rank.JACK),(Rank.KING, Rank.QUEEN), 
            (Rank.KING, Rank.JACK), (Rank.QUEEN, Rank.JACK)
        ]
    
    def get_action(self, game_state: GameState, hole_cards: List[Card], 
                   legal_actions: List[PlayerAction], min_bet: int, max_bet: int) -> tuple:
        """Play very conservatively - only strong hands"""
        
        if len(hole_cards) != 2:
            return PlayerAction.FOLD, 0
        
        card1, card2 = hole_cards
        
        # Check if we have a premium hand
        hand_tuple1 = (card1.rank, card2.rank)
        hand_tuple2 = (card2.rank, card1.rank)  # Check both orders
        
        is_premium = (hand_tuple1 in self.premium_hands or 
                     hand_tuple2 in self.premium_hands)
        
        # Also consider suited premium hands
        is_suited_premium = (card1.suit == card2.suit and 
                           (hand_tuple1 in self.premium_hands or 
                            hand_tuple2 in self.premium_hands))
        
        # Check for high pocket pairs
        is_high_pocket_pair = (card1.rank == card2.rank and 
                              card1.rank.value >= 7)  # 7s or better
        
        # Only play premium hands or high pocket pairs
        if not (is_premium or is_suited_premium or is_high_pocket_pair):
            return PlayerAction.FOLD, 0
        
        # We have a good hand - decide what to do
        pot_odds = GameInfoAPI.get_pot_odds(
            game_state.pot, 
            GameInfoAPI.calculate_bet_amount(game_state.current_bet, 
                                           game_state.player_bets[self.name])
        )
        
        # With premium hands, be aggressive
        if PlayerAction.RAISE in legal_actions:
            # Conservative raise - don't go too big
            current_pot = game_state.pot
            raise_amount = min(game_state.current_bet + current_pot // 2, max_bet)
            raise_amount = max(raise_amount, min_bet)  # Ensure minimum
            return PlayerAction.RAISE, raise_amount
        
        elif PlayerAction.CALL in legal_actions:
            # Always call with premium hands if we can't raise
            return PlayerAction.CALL, 0
        
        elif PlayerAction.CHECK in legal_actions:
            return PlayerAction.CHECK, 0
        
        # Shouldn't get here, but fold as fallback
        return PlayerAction.FOLD, 0
    
    def hand_complete(self, game_state: GameState, hand_result: Dict[str, Any]):
        """Track conservative play results"""
        self.hands_played += 1
        
        if 'winners' in hand_result and self.name in hand_result['winners']:
            self.hands_won += 1
        
        # Log statistics every 25 hands
        if self.hands_played % 25 == 0:
            win_rate = self.hands_won / self.hands_played if self.hands_played > 0 else 0
            self.logger.info(f"Conservative play: {self.hands_won}/{self.hands_played} wins ({win_rate:.2%})")