# -*- coding: utf-8 -*-
# @Author: Spencer H
# @Date:   2022-07-23
# @Last Modified by:   Spencer H
# @Last Modified date: 2022-07-23
# @Description:
"""

"""
import itertools
import random
from scipy.stats import norm


class _Player():
    """Base class for a blackjack player"""
    id_iter = itertools.count()

    def __init__(self, bank, double_allowed, das_allowed, surrender_allowed, verbose):
        self.ID = next(self.id_iter)
        self.bank = bank
        self.das_allowed = das_allowed
        self.double_allowed = double_allowed
        self.surrender_allowed = surrender_allowed
        self.verbose = verbose
        if self.verbose:
            print(f'::Player {self.ID} -- Initialited {self.TYPE}')

    def bet(self, *args):
        assert self.bank > 0
        bet = max(1, int(self.bet_frac * self.bank))
        if self.verbose:
            print(f'::Player {self.ID} -- Bet {bet}')
        return bet

    def action(self, obs):
        action = self._get_action(obs)
        if self.verbose:
            print(f'::Player {self.ID} -- chose action {action} on {obs}')
        return action

    def _get_action(self, obs):
        raise NotImplementedError

    def payout(self, payout):
        self.bank += payout
        if self.verbose:
            print(f'::Player {self.ID} -- Received payout of {payout}, bank={self.bank}')


class RandomAgent(_Player):
    """This agent is totally random
    
    Agent is only allowed to hit or stay
    """
    TYPE = 'RandomAgent'
    def __init__(self, bank, bet_frac=0.1, double_allowed=True, das_allowed=True, surrender_allowed=True, verbose=False):
        super().__init__(bank, double_allowed, das_allowed, surrender_allowed, verbose)
        self.bet_frac = bet_frac

    def _get_action(self, obs):
        tot = obs.hand.total
        if tot in [21]:
            return 'stay'
        else:
            return 'stay' if random.random() < 0.5 else 'hit'


class RiskBasedAgent(_Player):
    """This agent uses a notion of getting closer to 21
    
    Agent is only allowed to hit or stay
    """
    TYPE = 'RiskBasedAgent'
    def __init__(self, bank, bet_frac=0.1, risk_tol=0.50, double_allowed=True, das_allowed=True, surrender_allowed=True, verbose=False):
        """
        risk_tol - an agent hits of it is approx less than risk_tol*100 % of busting
        """
        super().__init__(bank, double_allowed, das_allowed, surrender_allowed, verbose)
        self.bet_frac = bet_frac
        self.risk_tol = risk_tol
        self.avg_card = 5.5    # np.mean(range(1,11))
        self.std_card = 2.872  # np.std(range(1,11))

    def _get_action(self, obs):
        tot = obs.hand.total
        is_soft = obs.hand.total
        if is_soft:
            return 'hit' if tot < 19 else 'stay'
        else:
            diff = 22 - tot
            prob_bust = 1 - norm.cdf(diff, self.avg_card, self.std_card)
            return 'hit' if prob_bust <= self.risk_tol else 'stay'


class BasicStrategyAgent(_Player):
    """This agent follows the 'basic strategy' philosophy"""
    TYPE = 'BasicStrategyAgent'
    def __init__(self, bank, bet_frac=0.1, double_allowed=True, das_allowed=True, surrender_allowed=True, verbose=False):
        super().__init__(bank, double_allowed, das_allowed, surrender_allowed, verbose)
        self.bet_frac = bet_frac

        # player's strategy based on total
        self.surrender = {15:{10:True}, 16:{9:True, 10:True, 'A':True}}
        self.split = {2:{2:'if_das', 3:'if_das', 4:True, 5:True, 6:True, 7:True},
                      3:{2:'if_das', 3:'if_das', 4:True, 5:True, 6:True, 7:True},
                      4:{5:'if_das', 6:'if_das'},
                      5:{},
                      6:{2:'if_das', 3:True, 4:True, 5:True, 6:True},
                      7:{2:True, 3:True, 4:True, 5:True, 6:True, 7:True},
                      8:{2:True, 3:True, 4:True, 5:True, 6:True, 7:True, 8:True, 9:True, 10:True, 'A':True},
                      9:{2:True, 3:True, 4:True, 5:True, 6:True, 8:True, 9:True},
                      10:{},
                      'A':{2:True, 3:True, 4:True, 5:True, 6:True, 7:True, 8:True, 9:True, 10:True, 'A':True}}
        self.double = {'soft':{13:{5:True, 6:True},
                               14:{5:True, 6:True},
                               15:{4:True, 5:True, 6:True},
                               16:{4:True, 5:True, 6:True},
                               17:{3:True, 4:True, 5:True, 6:True},
                               18:{2:True, 3:True, 4:True, 5:True, 6:True},
                               19:{6:True}},
                       'hard':{9: {3:True, 4:True, 5:True, 6:True},
                               10:{2:True, 3:True, 4:True, 5:True, 6:True, 7:True, 8:True, 9:True},
                               11:{2:True, 3:True, 4:True, 5:True, 6:True, 7:True, 8:True, 9:True, 10:True, 'A':True}}}
        self.hit_soft = {18:{9:True, 10:True, 'A':True},
                         19:{},
                         20:{}}
        self.hit_hard = {12:{2:True, 3:True, 7:True, 8:True, 9:True, 10:True, 'A':True},
                         13:{7:True, 8:True, 9:True, 10:True, 'A':True},
                         14:{7:True, 8:True, 9:True, 10:True, 'A':True},
                         15:{7:True, 8:True, 9:True, 10:True, 'A':True},
                         16:{7:True, 8:True, 9:True, 10:True, 'A':True}}

    def _get_action(self, obs):
        hand = obs.hand
        tot = obs.hand.total
        n_cards = len(obs.hand)
        is_soft = obs.hand.is_soft
        duc = obs.dealer_upcard

        # -- auto stay
        if tot in [20, 21]:
            return 'stay'

        # -- check surrender
        if self.surrender_allowed and (n_cards == 2) and (not is_soft) and (tot in self.surrender):
            surr = self.surrender[tot].get(duc, False)
            if surr:
                return 'surrender'

        # -- check split
        # TODO: ONLY IF ENOUGH MONEY
        if (n_cards == 2) and (hand[0]==hand[1]):
            split = self.split[hand[0]].get(duc, False)
            if split or (split=='if_das' and self.das_allowed):
                return 'split'

        # -- check double down
        # TODO: ONLY IF ENOUGH MONEY
        if self.double_allowed and (n_cards == 2):
            stat = 'soft' if is_soft else 'hard'
            if tot in self.double[stat]:
                double = self.double[stat][tot].get(duc, False)
            else:
                double = False
            if double:
                return 'double'

        # -- check remaining strategy
        if is_soft:
            if tot <= 17:
                hit = True
            elif tot >= 20:
                hit = False
            else:
                hit = self.hit_soft[tot].get(duc, False)
        else:
            if tot <= 11:
                hit = True
            elif tot >= 17:
                hit = False
            else:
                hit = self.hit_hard[tot].get(duc, False)
        if hit:
            return 'hit'
        else:
            return 'stay'