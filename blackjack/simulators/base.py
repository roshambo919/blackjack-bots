# -*- coding: utf-8 -*-
# @Author: Spencer H
# @Date:   2022-07-23
# @Last Modified by:   Spencer H
# @Last Modified date: 2022-07-23
# @Description:
"""

"""

import random


class Hand():
    def __init__(self, *args):
        self.hand = []
        for c in args:
            self.hand.append(c)

    def __len__(self):
        return len(self.hand)

    def __getitem__(self, idx):
        return self.hand[idx]

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f'Hand of {self.hand}, total={self.total}'

    @property
    def total(self):
        return total(self.hand)[0]

    @property
    def bust(self):
        return self.total > 21

    @property
    def is_soft(self):
        return total(self.hand)[1]

    @property
    def blackjack(self):
        return (len(self)==2) and (self.total==21)


    def append(self, c):
        if c in ['j', 'J', 'q', 'Q', 'k', 'K']:
            c = 10
        self.hand.append(c)

    def split(self):
        if self.hand[0] != self.hand[1]:
            raise RuntimeError(f'Cannot split hand of {self.hand[0]}, {self.hand[1]}')
        else:
            return Hand(self.hand[0]), Hand(self.hand[1])


def total(hand):
    """Get the total of a hand

    takes advantage of the fact that only 1 ace could ever be an 11"""
    t = 0
    n_aces = 0
    ace_as_11 = False
    for c in hand:
        if c in list(range(2, 11, 1)):
            t += c
        elif c in ['a', 'A']:
            if (t + 11) <= 21:
                t += 11
                ace_as_11 = True
            else:
                t += 1
        else:
            raise RuntimeError(f'Cannot process card of {c}')
    if (t > 21) and  ace_as_11:
        t -= 10
    return t, ace_as_11


class Observation():
    def __init__(self, duc, hand):
        self.dealer_upcard = duc if duc not in ['J', 'Q', 'K'] else 10
        self.hand = hand

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f'Observation of duc: {self.dealer_upcard}, {self.hand}'


class Deck():
    """Base class for a deck"""
    def __init__(self, n=1):
        self.n = n
        self._reset_deck()
        self.full_len = len(self)

    def __len__(self):
        return len(self.cards)

    def _reset_deck(self):
        raise NotImplementedError

    def shuffle(self):
        self._reset_deck()
        random.shuffle(self.cards)

    def draw(self):
        return self.cards.pop()


class SmoothDeck(Deck):
    """
    A smooth card deck being one where J, Q, K replaced by 10
    """
    def _reset_deck(self):
        self.cards = list(range(2,11))
        self.cards.extend([10,10,10,'A'])  # J, Q, K represented as 10
        self.cards *= (4*self.n)


class BlackjackGame():
    def __init__(self, n_decks=4, verbose=False):
        self.players = {}
        self.hands = {}
        self.bets = {}
        self.deck = SmoothDeck(n=n_decks)
        self.pct_shuffle = 0.25  # once the deck gets to below this number of original
        self.round = 0
        self.verbose = verbose

    @property
    def need_shuffle(self):
        return (self.deck.full_len-len(self.deck)) / self.deck.full_len <= self.pct_shuffle

    @property
    def n_players_in(self):
        return sum([p.bank > 0 for p in self.players.values()])

    def add_player(self, player):
        self.players[player.ID] = player

    def play_round(self):
        self.round += 1
        if self.verbose:
            print(f'::Game -- round {self.round}')

        if self.need_shuffle:
            self.deck.shuffle()

        # -- only allow players with money
        self.players = {ID:p for ID, p in self.players.items() if p.bank > 0}

        # -- take bets
        for ID, p in self.players.items():
            self.bets[ID] = p.bet()

        # -- deal
        self.hands = {}
        for ID in self.players:
            self.hands[ID] = [Hand(self.deck.draw(), self.deck.draw())]
        self.hands['dealer'] = Hand(self.deck.draw(), self.deck.draw())

        # -- check dealer blackjack
        if self.hands['dealer'].blackjack:
            for ID, p in self.players.items():
                payout = sum([-self.bets[ID] if h.total < 21 else 0 for h in self.hands[ID]])
                p.payout(payout)
        else:
            # -- play hands
            for ID, p in self.players.items():
                remove_hands = []
                # for i, h in enumerate(self.hands[ID]):
                i = 0
                while i < len(self.hands[ID]):
                    h = self.hands[ID][i] 
                    while not h.bust:
                        obs = Observation(self.hands['dealer'][0], h)
                        action = p.action(obs)
                        if action == 'surrender':
                            p.payout(-round(self.bets[ID]/2))
                            remove_hands.append(h)
                            break
                        elif action == 'split':
                            h_1, h_2 = h.split()
                            h_1.append(self.deck.draw())
                            h_2.append(self.deck.draw())
                            self.hands[ID][i] = h_1
                            h = h_1
                            self.hands[ID].append(h_2)
                        elif action == 'double':
                            self.bets[ID] *= 2
                            h.append(self.deck.draw())
                            break
                        elif action == 'hit':
                            h.append(self.deck.draw())
                        elif action == 'stay':
                            break
                        else:
                            raise NotImplementedError(action)
                    i += 1
                    if self.verbose:
                        print(f'::Player {ID} -- hand {i+1} ended up {h}')
                for h in remove_hands:
                    self.hands[ID].remove(h)

            # -- player dealer
            if not all([h.bust or h.blackjack for ID, hands in self.hands.items() for h in hands if ID != 'dealer']):
                self._play_dealer()
                if self.verbose:
                    print(f'::Dealer - played out hand to {self.hands["dealer"]}')
            else:
                if self.verbose:
                    print(f'::Dealer - did not need to play since all players terminal')

            # -- compare results
            d = self.hands['dealer']
            for ID, p in self.players.items():
                payout = 0
                for h in self.hands[ID]:
                    if h.blackjack:
                        payout += round(1.5 * self.bets[ID])
                    else:
                        if h.bust:
                            payout -= self.bets[ID]  # even if dealer busted
                        else:
                            if d.bust or (h.total > d.total):
                                payout += self.bets[ID]
                            elif h.total == d.total:
                                pass
                            else:
                                payout -= self.bets[ID]
                p.payout(payout)

            # -- shuffle, if needed


    def _play_dealer(self):
        """Dealer always hits until 17"""
        while self.hands['dealer'].total < 17:
            self.hands['dealer'].append(self.deck.draw())