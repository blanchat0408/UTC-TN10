from random import randint
from fuzzy import effi_dis, effi_char


def battery(prixVente: list, diff: list, prixElec: list, Bat=None):
    class Battery:
        SoCmin = 0.2
        SoCmax = 0.8
        Pmax = 5
        cap = 40
        Pdis = [0] * 24
        Pchar = [0] * 24

        def __init__(self, batt):
            if not batt:
                self.SoC = [0] * 24
                self.SoC[0] = randint(20, 30) / 100
                self.mode: list[str] = [None] * 23  # "charge" & "discharge"
            else:
                self.SoC = batt.SoC
                self.Pchar = batt.Pchar
                self.mode = batt.mode

    bat = Battery(Bat)
    for t in range(23):
        dis_bat = effi_dis(prixElec[t], bat.SoC[t], 8.7, 12.2, 16.2, 18.2)
        char_bat = effi_char(prixVente[t], bat.SoC[t], 8.7 * 0.8, 12.2 * 0.8, 16.2 * 0.8, 18.2 * 0.8)
        if not bat.mode[t]:
            if diff[t] <= 0:
                # discharge battery
                bat.mode[t] = "discharge"
                if bat.SoC[t] <= bat.SoCmin:
                    bat.Pdis[t] = 0
                else:
                    bat.Pdis[t] = round(min(bat.Pmax, abs(diff[t]), (bat.SoC[t] - bat.SoCmin) * bat.cap) * dis_bat, 2)
            else:
                # charge battery
                bat.mode[t] = "charge"
                if bat.SoC[t] >= bat.SoCmax:
                    bat.Pchar[t] = 0
                else:
                    bat.Pchar[t] = round(min(bat.Pmax, diff[t], (bat.SoCmax - bat.SoC[t]) * bat.cap) * char_bat, 2)
            bat.SoC[t + 1] = round(bat.SoC[t] + ((bat.Pchar[t] * 0.85 - bat.Pdis[t] * 1) / bat.cap), 2)
        elif bat.mode[t] == "charge":
            Pchar = bat.Pchar[t]
            char_bat_ex = effi_char((prixVente[t] + prixElec[t]) / 2, bat.SoC[t], 8.7, 12.2, 16.2, 18.2)
            if bat.SoC[t] >= bat.SoCmax:
                bat.Pchar[t] = 0
            else:
                bat.Pchar[t] = round(min(bat.Pmax, diff[t], (bat.SoCmax - bat.SoC[t]) * bat.cap)
                                     * char_bat_ex, 2)
            Pchar += bat.Pchar[t]
            bat.SoC[t + 1] = round(bat.SoC[t] + (Pchar * 0.85) / bat.cap, 2)
        else:
            pass
    return bat


def ElecV(prixElec: list, prixVente: list, starttime: int, leavetime: int, EV=None, QC=None):
    class Ev:
        cap = 20
        Pmax = 5
        SoCmax = 1

        def __init__(self, Elecv):
            if Elecv is None:
                self.SoC = [0] * 24
                for t_arr in range(24):
                    if t_arr == starttime:
                        self.SoC[t_arr] = randint(20, 80) / 100
                        self.Pchar = [0] * 24
                        break
            else:
                self.SoC = Elecv.SoC
                print(self.SoC)
                self.Pchar = Elecv.Pchar
                self.Pchar_ex = [0] * 24

    ev = Ev(EV)
    print(f"QC = {QC}")
    for t in range(23):
        if QC is None:
            char_ev = effi_char(prixElec[t], ev.SoC[t], 8.7, 12.2, 16.2, 18.2)
            if starttime <= t < leavetime and ev.SoC[t] < ev.SoCmax:
                ev.Pchar[t] = round(min(ev.Pmax, (1 - ev.SoC[t]) * ev.cap) * char_ev, 2)
                ev.SoC[t + 1] = round(ev.SoC[t] + ev.Pchar[t] / ev.cap, 2)
        elif QC is not None:
            print(f"{t}")
            char_ev_ex = effi_char((prixVente[t] + prixElec[t]) / 2, ev.SoC[t], 8.7, 12.2, 16.2, 18.2)
            if starttime <= t < leavetime and ev.SoC[t] < ev.SoCmax:
                print(round(min(ev.Pmax, (1 - ev.SoC[t]) * ev.cap - ev.Pchar[t], QC[t]) * char_ev_ex, 2))
                ev.Pchar_ex[t] = round(min(ev.Pmax, (1 - ev.SoC[t]) * ev.cap - ev.Pchar[t], QC[t]) * char_ev_ex, 2)
                Pchar = ev.Pchar_ex[t] + ev.Pchar[t]
                ev.SoC[t + 1] = round(ev.SoC[t] + Pchar / ev.cap, 2)
            elif ev.SoC[t] >= ev.SoCmax:
                break
    return ev


def devices(prixElec: list, prixVente: list, starttime: int, leavetime: int,
            consommation=None, production=None, QC=None, Bat=None, EV=None):
    ev = ElecV(prixElec, prixVente, starttime, leavetime, EV, QC)
    if QC is None:
        diff = [production[t] - consommation[t] - ev.Pchar[t] for t in range(23)]
        bat = battery(prixVente, diff, prixElec, Bat)
        return bat, ev
    else:
        diff = [QC[t] - ev.Pchar_ex[t] for t in range(23)]
        bat = battery(prixVente, diff, prixElec, Bat)
        QUC = [round(diff[t] - bat.Pchar[t], 2) for t in range(23)]
        return bat, ev, QUC
