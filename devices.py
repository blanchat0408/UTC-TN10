# use it only with ver4.1.py

from random import randint
from fuzzy import effi_dis, effi_char


def battery(prixVente: list, diff: list, prixElec: list, Bat=None, mode=None):
    class Battery:
        SoCmin = 0.2
        SoCmax = 0.8
        Pmax = 5
        cap = 40
        Pdis = [0] * 24
        Pchar = [0] * 24
        lack = [0] * 24

        def __init__(self, batt):
            if not batt:
                self.SoC = [0] * 24
                self.SoC[0] = randint(20, 30) / 100
            else:
                self.SoC = batt.SoC
                self.Pchar = batt.Pchar
                self.Pchar_ex = [0] * 24
                self.lack = batt.lack
                self.UE = [0] * 24  # énergie utilisé

    bat = Battery(Bat)
    for t in range(23):
        dis_bat = effi_dis(prixElec[t], bat.SoC[t], 8.7, 12.2, 16.2, 18.2)
        char_bat = effi_char(prixVente[t], bat.SoC[t], 8.7, 12.2, 16.2, 18.2)
        char_bat_ex = effi_char((prixVente[t] + prixElec[t]) / 2, bat.SoC[t], 8.7, 12.2, 16.2, 18.2)
        if not Bat:
            if diff[t] <= 0:
                bat.lack[t] = abs(diff[t])
            elif diff[t] > 0:
                # charge battery
                if bat.SoC[t] >= bat.SoCmax:
                    bat.Pchar[t] = 0
                else:
                    bat.Pchar[t] = round(min(bat.Pmax, diff[t], (bat.SoCmax - bat.SoC[t]) * bat.cap) * char_bat, 2)
            bat.SoC[t + 1] = round(bat.SoC[t] + bat.Pchar[t] * 0.85 / bat.cap, 2)
        else:
            if mode[t] == 1:
                bat.lack[t] = 0
                if bat.SoC[t] >= bat.SoCmax:
                    bat.Pchar_ex[t] = 0
                else:
                    bat.Pchar_ex[t] = round(min(bat.Pmax, diff[t], (bat.SoCmax - bat.SoC[t]) * bat.cap) * char_bat_ex, 2)
                bat.UE[t] += bat.Pchar_ex[t]
            elif mode[t] == 0:
                if diff[t] >= bat.lack[t]:
                    reste = diff[t] - bat.lack[t]
                    bat.UE[t] += bat.lack[t]
                    bat.lack[t] = 0
                    if bat.SoC[t] >= bat.SoCmax:
                        bat.Pchar_ex[t] = 0
                    else:
                        bat.Pchar_ex[t] = round(min(bat.Pmax, reste, (bat.SoCmax - bat.SoC[t]) * bat.cap) * char_bat_ex, 2)
                    bat.UE[t] += bat.Pchar_ex[t]
                elif 0 < diff[t] < bat.lack[t]:
                    bat.lack[t] -= diff[t]
                    bat.UE[t] += diff[t]
                elif diff[t] == 0:
                    bat.UE[t] += 0
                    if bat.lack[t] > 0:  # Il faut discharger.
                        if bat.SoC[t] <= bat.SoCmin:
                            bat.Pdis[t] = 0
                        else:
                            bat.Pdis[t] = round(
                                min(bat.Pmax, bat.lack[t], (bat.SoC[t] - bat.SoCmin) * bat.cap) * dis_bat,
                                2)
                    else:
                        pass
            Pdis = bat.Pdis[t]
            Pchar = bat.Pchar[t] + bat.Pchar_ex[t]
            for i in range(t, 23):
                bat.SoC[t + 1] = round(bat.SoC[t] + (Pchar * 0.85 - Pdis * 1) / bat.cap, 2)
    return bat


def ElecV(prixElec: list, prixVente: list, starttime: int, leavetime: int, EV=None, QC=None, mode=None):
    class Ev:
        cap = 20
        Pmax = 5
        SoCmax = 1

        def __init__(self, Elecv=None):
            if Elecv is None:
                self.SoC = [0] * 24
                self.SoC[starttime] = randint(20, 80) / 100
                self.Pchar = [0] * 24

            else:
                self.SoC = Elecv.SoC
                self.Pchar = Elecv.Pchar
                self.Pchar_ex = [0] * 24

    ev = Ev(EV)
    for t in range(23):
        if not EV:
            char_ev = effi_char(prixElec[t], ev.SoC[t], 8.7, 12.2, 16.2, 18.2)
            if starttime <= t < leavetime and ev.SoC[t] < ev.SoCmax:
                    ev.Pchar[t] = round(min(ev.Pmax, (1 - ev.SoC[t]) * ev.cap) * char_ev, 2)
                    ev.SoC[t + 1] = round(ev.SoC[t] + ev.Pchar[t] / ev.cap, 2)
        else:
            if mode[t] == 1:
                char_ev_ex = effi_char((prixVente[t] + prixElec[t]) / 2, ev.SoC[t], 8.7, 12.2, 16.2, 18.2)
                if starttime <= t < leavetime and ev.SoC[t] < ev.SoCmax:
                    ev.Pchar_ex[t] = round(min(ev.Pmax, (1 - ev.SoC[t]) * ev.cap - ev.Pchar[t], QC[t]) * char_ev_ex, 2)
                    Pchar = ev.Pchar_ex[t] + ev.Pchar[t]
                    ev.SoC[t + 1] = round(ev.SoC[t] + Pchar / ev.cap, 2)
                elif ev.SoC[t] >= ev.SoCmax:
                    break
            elif mode[t] == 0:
                pass
    return ev


def devices(prixElec: list, prixVente: list, starttime: int, leavetime: int,
            consommation=None, production=None, QC=None, Bat=None, EV=None, mode=None):
    ev = ElecV(prixElec, prixVente, starttime, leavetime, EV, QC, mode)
    if QC is None:
        diff = [production[t] - consommation[t] - ev.Pchar[t] for t in range(23)]
        bat = battery(prixVente, diff, prixElec, Bat)
        return bat, ev
    else:
        QR = [QC[t] - ev.Pchar_ex[t] for t in range(24)]
        bat = battery(prixVente, QR, prixElec, Bat, mode)
        QR = [QC[t] - bat.UE[t] for t in range(24)]
        return bat, ev, QR
