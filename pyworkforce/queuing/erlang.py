from math import exp, ceil, floor


class ErlangC:
    def __init__(self, transactions: float, asa: float, aht: float,
                 interval: int = None, shrinkage=0.0,
                 **kwargs):
        """
        Computes the number of positions required fo attend a number of transactions in a queue system based on ErlangC
        Implementation based on: https://lucidmanager.org/data-science/call-centre-workforce-planning-erlang-c-in-r/

        :param transactions: number of total transactions that comes in
        :param aht: average handling time of a transaction (minutes)
        :param interval: Interval length (minutes)
        :param shrinkage: Percentage of time that an operator unit is not available
        """
        self.n_transactions = transactions
        self.asa = asa
        self.aht = aht
        self.interval = interval
        self.intensity = (self.n_transactions / self.interval) * self.aht
        self.shrinkage = shrinkage

    def waiting_probability(self, positions, scale_positions=False):
        """
        :param positions: Number of positions to attend the transactions
        :param scale_positions: True if the positions where calculated using shrinkage
        :return: the probability of a transaction waits in queue
        """
        if scale_positions:
            productive_positions = floor((1 - self.shrinkage) * positions)
        else:
            productive_positions = positions

        erlang_b_inverse = 1
        for agent in range(1, productive_positions + 1):
            erlang_b_inverse = 1 + (erlang_b_inverse * agent / self.intensity)

        erlang_b = 1 / erlang_b_inverse
        return productive_positions * erlang_b / (productive_positions - self.intensity * (1 - erlang_b))

    def service_level(self, positions, scale_positions=False):
        """
        :param positions: Number of positions attending
        :param scale_positions: True if the positions where calculated using shrinkage
        :return: achieved service level
        """
        if scale_positions:
            productive_positions = floor((1 - self.shrinkage) * positions)
        else:
            productive_positions = positions

        probability_wait = self.waiting_probability(productive_positions, scale_positions=False)
        exponential = exp(-(productive_positions - self.intensity) * (self.asa / self.aht))
        return max(0, 1 - (probability_wait * exponential))

    def achieved_occupancy(self, positions, scale_positions=False):
        """
        :param positions: Number of raw positions
        :param scale_positions: True if the positions where calculated using shrinkage
        :return: Expected occupancy of positions
        """
        if scale_positions:
            productive_positions = floor((1 - self.shrinkage) * positions)
        else:
            productive_positions = positions
        return self.intensity/productive_positions

    def required_positions(self, service_level):
        """
        :param service_level: Target service level
        :return: Number of positions needed to ensure the required service level
        """
        positions = round(self.intensity + 1)
        achieved_sla = self.service_level(positions, scale_positions=False)
        while achieved_sla < service_level:
            positions += 1
            achieved_sla = self.service_level(positions, scale_positions=False)

        achieved_occupancy = self.achieved_occupancy(positions, scale_positions=False)
        raw_positions = ceil(positions)
        positions = ceil(raw_positions / (1 - self.shrinkage))

        return {"raw_positions": raw_positions,
                "positions": positions,
                "service_level": achieved_sla,
                "occupancy": achieved_occupancy}
