# -*- coding: utf-8 -*-
# @Author: Spencer H
# @Date:   2022-07-23
# @Last Modified by:   Spencer H
# @Last Modified date: 2022-07-23
# @Description:
"""

"""

import random
from blackjack import BlackjackGame
from blackjack.bots import RandomAgent, RiskBasedAgent, BasicStrategyAgent


random.seed(5)


def main():
    # game parameters
    M_0 = 50
    bet_frac = 0.1
    risk_tol = 0.25
    double_allowed = True
    das_allowed = True
    surrender_allowed = True
    verbose = True

    # initialization
    game = BlackjackGame(n_decks=4, verbose=verbose)
    player_1 = RandomAgent(M_0, bet_frac, double_allowed, das_allowed, surrender_allowed, verbose)
    player_2 = RiskBasedAgent(M_0, bet_frac, risk_tol, double_allowed, das_allowed, surrender_allowed, verbose)
    player_3 = RiskBasedAgent(M_0, bet_frac, risk_tol, double_allowed, das_allowed, surrender_allowed, verbose)
    player_4 = BasicStrategyAgent(M_0, bet_frac, double_allowed, das_allowed, surrender_allowed, verbose)

    game.add_player(player_1)
    game.add_player(player_2)
    game.add_player(player_3)
    game.add_player(player_4)

    # gameplay
    while game.n_players_in > 0:
        game.play_round()


if __name__ == "__main__":
    main()