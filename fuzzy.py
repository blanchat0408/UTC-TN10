import numpy


class Fuzzification:
    s = 0

    def __init__(self, prix, soc, lower, low, high, higher):
        self.prix = prix
        self.soc = soc
        self.lower = lower
        self.low = low
        self.high = high
        self.higher = higher

    def low(self):
        if self.soc < 0.25:
            low = 1
        elif 0.25 <= self.soc <= 0.4:
            low = numpy.poly1d(numpy.polyfit((0.25, 0.4), (1, 0), 1))(self.soc)
        else:
            low = 0
        return low

    def medium(self):
        if 0.25 <= self.soc <= 0.4:
            medium = numpy.poly1d(numpy.polyfit((0.25, 0.4), (0, 1), 1))(self.soc)
        elif 0.4 < self.soc < 0.6:
            medium = 1
        elif 0.6 <= self.soc <= 0.75:
            medium = numpy.poly1d(numpy.polyfit((0.6, 0.75), (1, 0), 1))(self.soc)
        else:
            medium = 0
        return medium

    def high(self):
        if self.soc > 0.75:
            high = 1
        elif 0.6 <= self.soc <= 0.75:
            high = numpy.poly1d(numpy.polyfit((0.6, 0.75), (0, 1), 1))(self.soc)
        else:
            high = 0
        return high

    def highprix(self):
        if self.high <= self.prix <= self.higher:
            x = (self.high, self.higher)
            y = (0, 1)
            hp = numpy.poly1d(numpy.polyfit(x, y, 1))(self.prix)
        elif self.prix < self.high:
            hp = 0
        else:
            hp = 1
        return hp

    def normalprix(self):
        if self.low <= self.prix <= self.high:
            np = 1
        elif self.lower < self.prix < self.low:
            x = (self.lower, self.low)
            y = (0, 1)
            np = numpy.poly1d(numpy.polyfit(x, y, 1))(self.prix)
        elif self.higher > self.prix > self.high:
            x = (self.high, self.higher)
            y = (1, 0)
            np = numpy.poly1d(numpy.polyfit(x, y, 1))(self.prix)
        else:
            np = 0
        return np

    def lowprix(self):
        if self.prix < self.lower:
            lp = 1
        elif self.lower <= self.prix <= self.low:
            x = numpy.array([self.lower, self.low])
            y = numpy.array([1, 0])
            lp = numpy.poly1d(numpy.polyfit(x, y, 1))(self.prix)
        else:
            lp = 0
        return lp


class RulesDecharge(Fuzzification):

    def __init__(self, prix, soc, lower, low, high, higher):
        super().__init__(prix, soc, lower, low, high, higher)
        self.fe = self.faster()
        self.f = self.fast()
        self.m = self.moyenne()
        self.s = self.slow()
        self.no = self.stop()

    def faster(self):
        fe = [min(super().highprix(), super().high())]
        return fe

    def fast(self):
        f = [min(super().highprix(), super().medium()), min(super().normalprix(), super().high())]
        return f

    def moyenne(self):
        m = [min(super().highprix(), super().low()), min(super().normalprix(), super().medium()),
             min(super().lowprix(), super().high())]
        return m

    def slow(self):
        s = [min(super().normalprix(), super().low()), min(super().lowprix(), super().medium())]
        return s

    def stop(self):
        no = [min(super().low(), super().lowprix())]
        return no


class RulesCharge(Fuzzification):
    def __init__(self, prix, soc, lower, low, high, higher):
        super().__init__(prix, soc, lower, low, high, higher)
        self.fe = self.faster()
        self.f = self.fast()
        self.m = self.moyenne()
        self.s = self.slow()
        self.no = self.stop()

    def faster(self):
        fe = [min(super().low(), super().lowprix())]
        return fe

    def fast(self):
        f = [min(super().normalprix(), super().low()), min(super().lowprix(), super().medium())]
        return f

    def moyenne(self):
        m = [min(super().highprix(), super().low()), min(super().normalprix(), super().medium()),
             min(super().lowprix(), super().high())]
        return m

    def slow(self):
        s = [min(super().highprix(), super().medium()), min(super().normalprix(), super().high())]
        return s

    def stop(self):
        no = [min(super().highprix(), super().high())]
        return no


def effi_dis(prix, soc, lower, low, high, higer):
    dis = RulesDecharge(prix, soc, lower, low, high, higer)

    res = round((sum(dis.fe) * 1 + sum(dis.f) * 0.75 + sum(dis.m) * 0.5 + sum(dis.s) * 0.25 + sum(dis.no) * 0) / (
            sum(dis.fe) + sum(dis.f) + sum(dis.m) + sum(dis.s) + sum(dis.no)), 2)
    return res


def effi_char(prix, soc, lower, low, high, higher):
    char = RulesCharge(prix, soc, lower, low, high, higher)

    res = round((sum(char.fe) * 1 + sum(char.f) * 0.75 + sum(char.m) * 0.5 + sum(char.s) * 0.25 + sum(char.no) * 0) / (
            sum(char.fe) + sum(char.f) + sum(char.m) + sum(char.s) + sum(char.no)), 2)
    return res


def main():
    effi = effi_dis(19, 0.22, 8.7, 12.2, 16.2, 18.2)
    print(effi)


if __name__ == "__main__":
    main()
