# version with fuzzy logic
# for battery & EV

from random import randint
from ast import literal_eval
import matplotlib.pyplot as plt

import spade
from spade.agent import Agent
from spade.message import Message
from spade.behaviour import CyclicBehaviour, OneShotBehaviour

from fuzzy import effi_dis, effi_char

path = f"D:/Users/shiguang/Documents/Stage202309_SHI_Guangyu/data_stage/"


def devices(consommation: list, production: list, prixElec: list, prixVente: list, starttime: int, leavetime: int):
    class Battery:
        SoCmin = 0.2
        SoCmax = 0.8
        Pmax = 5
        cap = 40
        SoC: list[float] = [0] * 24
        Pdis: list[float] = [0] * 24
        Pchar: list[float] = [0] * 24

        def __init__(self):
            self.SoC[0] = randint(20, 30) / 100

    class Ev:
        cap = 20
        Pmax = 5
        SoCmax = 1
        SoC = [0] * 24
        Pchar: list[float] = [0] * 24

    bat = Battery()
    ev = Ev()
    diff = [0] * 24

    for t in range(23):
        dis_bat = effi_dis(prixElec[t], bat.SoC[t], 8.7, 12.2, 16.2, 18.2)
        char_bat = effi_char(prixVente[t], bat.SoC[t], 8.7 * 0.9, 12.2 * 0.9, 16.2 * 0.9, 18.2 * 0.9)
        if starttime <= t < leavetime and ev.SoC[t] < ev.SoCmax:
            if t == starttime:
                ev.SoC[t] = randint(20, 80) / 100

            char_ev = effi_char(prixVente[t], ev.SoC[t], 8.7, 12.2, 16.2, 18.2)

            ev.Pchar[t] = round(min(ev.Pmax, (1 - ev.SoC[t]) * ev.cap) * char_ev, 2)
            ev.SoC[t + 1] = round(ev.SoC[t] + ev.Pchar[t] / ev.cap, 2)

        diff[t] = production[t] - consommation[t] - ev.Pchar[t]

        if diff[t] <= 0:
            # discharge battery
            if bat.SoC[t] <= bat.SoCmin:
                bat.Pdis[t] = 0
            else:
                bat.Pdis[t] = round(min(bat.Pmax, abs(diff[t]), (bat.SoC[t] - bat.SoCmin) * bat.cap) * dis_bat, 2)
        else:
            # charge battery
            if bat.SoC[t] >= bat.SoCmax:
                bat.Pchar[t] = 0
            else:
                bat.Pchar[t] = round(min(bat.Pmax, diff[t], (bat.SoCmax - bat.SoC[t]) * bat.cap) * char_bat, 2)
        bat.SoC[t + 1] = round(bat.SoC[t] + ((bat.Pchar[t] * 0.85 - bat.Pdis[t] * 1) / bat.cap), 2)
    return bat, ev


class Maison(Agent):
    c_t = [0] * 24
    p_t = [0] * 24

    class Initialization(OneShotBehaviour):
        async def run(self) -> None:

            for t in range(24):
                if 0 <= t < 6:
                    self.agent.consommation.append(0)
                elif 6 <= t <= 16:
                    self.agent.consommation.append(randint(1, 3))
                elif 16 < t <= 23:
                    self.agent.consommation.append(randint(3, 4))

            for t in range(24):
                if 0 <= t < 8 or 19 < t <= 23:
                    self.agent.production.append(0)
                elif 8 <= t <= 19:
                    self.agent.production.append(randint(5, 6))

            starttime = randint(7, 17)
            leavetime = randint(starttime+1, 18)
            self.agent.battery, self.agent.ev = (devices(self.agent.consommation, self.agent.production,
                                                         self.agent.prixlist, self.agent.venteprix,
                                                         starttime, leavetime))

            fig_profil = plt.figure("profil")
            # figure de consommation
            print(f"Consommation: {self.agent.consommation}")
            fig_c = fig_profil.add_subplot(2, 1, 1)
            fig_c.plot(range(24), self.agent.consommation)
            plt.title(f"{self.agent.name}_Consommation")

            # figure de production
            print(f"Production: {self.agent.production}")
            fig_p = plt.subplot(2, 1, 2)
            fig_p.plot(range(24), self.agent.production)
            plt.title(f"{self.agent.name}_Production")
            plt.savefig(path + "figure/" + "profil.png")
            plt.show()

            fig_de_battery = plt.figure("batterie")
            # figure de batterie
            print(f"Battery SoC: {self.agent.battery.SoC}")
            fig_bat_soc = plt.subplot(3, 1, 1)
            fig_bat_soc.plot(range(24), self.agent.battery.SoC)
            plt.title(f"{self.agent.name}_Bat_SoC")
            print(f"Battery charge power: {self.agent.battery.Pchar}")
            fig_bat_char = plt.subplot(3, 1, 2)
            fig_bat_char.plot(range(24), self.agent.battery.Pchar)
            plt.title(f"{self.agent.name}_Bat_Charge")
            print(f"Battery discharge power: {self.agent.battery.Pdis}")
            fig_bat_char = plt.subplot(3, 1, 3)
            fig_bat_char.plot(range(24), self.agent.battery.Pdis)
            plt.title(f"{self.agent.name}_Bat_Discharge")
            plt.savefig(path + "figure/" + "batterie.png")
            plt.show()

            # figure de EV
            fig_de_EV = plt.figure("EV")
            print(f"EV SoC:{self.agent.ev.SoC}")
            fig_ev_soc = plt.subplot(2, 1, 1)
            fig_ev_soc.plot(range(24), self.agent.ev.SoC)
            plt.title(f"{self.agent.name}_EV_SoC")
            print(f"EV power:{self.agent.ev.Pchar}")
            fig_ev_char = plt.subplot(2, 1, 2)
            fig_ev_char.plot(range(24), self.agent.ev.Pchar)
            plt.title(f"{self.agent.name}_EV_Charge")
            plt.savefig(path + "figure/" + "EV.png")
            plt.show()

            # consommation excess & production excess
            for t in range(24):
                diff = self.agent.production[t] - self.agent.consommation[t] - self.agent.ev.Pchar[t]
                if diff < 0:
                    self.agent.consommation_excess.append(round(abs(diff) - self.agent.battery.Pdis[t], 2))
                    self.agent.production_excess.append(0)
                else:
                    self.agent.consommation_excess.append(0)
                    self.agent.production_excess.append(round(diff - self.agent.battery.Pchar[t], 2))


            fig_a_envoyer = plt.figure("excess")
            # print(f"Battery discharge: {self.agent.battery.Pdis}")
            # figure de consommation excess
            print(f"Consommation excess: {self.agent.consommation_excess}")
            fig_pdis = plt.subplot(2, 1, 1)
            fig_pdis.plot(range(24), self.agent.consommation_excess, marker='o')
            plt.title(f"{self.agent.name}_Consommation excess")

            # figure de production excess
            print(f"Production excess: {self.agent.production_excess}")
            fig_pc = plt.subplot(2, 1, 2)
            fig_pc.plot(range(24), self.agent.production_excess, marker='o')
            plt.title(f"{self.agent.name}_Production excess")
            plt.savefig(path + "figure/" + "excess.png")
            plt.show()

        async def on_end(self) -> None:
            self.agent.add_behaviour(self.agent.SaveData())
            self.agent.add_behaviour(self.agent.SendData())
            self.agent.add_behaviour(self.agent.ReceData())

    class SaveData(OneShotBehaviour):

        async def run(self) -> None:
            import pandas as pd
            import os.path
            data_profil = pd.DataFrame([self.agent.prixlist, self.agent.venteprix,
                                        self.agent.consommation, self.agent.production,
                                        self.agent.battery.SoC, self.agent.battery.Pchar, self.agent.battery.Pdis,
                                        self.agent.ev.SoC, self.agent.ev.Pchar,
                                        self.agent.consommation_excess,self.agent.production_excess],
                                       index=["buy price", "sell price",
                                              "consumption", "production",
                                              "battery SoC", "Power charge", "Power discharge",
                                              "EV SoC", "Power charge",
                                              "Consumption excess", "¨Production excess"],
                                       columns=range(24))
            # print(data_profil)
            # path = f"D:/Users/shiguang/Documents/Stage202309_SHI_Guangyu/data_stage/{self.agent.name}.xlsx"
            path_data = path +  f"{self.agent.name}.xlsx"
            if os.path.isfile(path_data):
                with pd.ExcelWriter(path_data, mode="a", if_sheet_exists='new') as writer:
                    data_profil.to_excel(writer)
            else:
                data_profil.to_excel(path_data, float_format="%.2f")

    class MkConnection(OneShotBehaviour):
        async def run(self) -> None:
            msg = Message(to="spade01@jabbim.com")
            msg.body = "Is Aggregator here ?"
            await self.send(msg)
            print("Making Connection")
            rep = await self.receive(timeout=10)
            if rep:
                print(rep.body)
                print("Connected")
            else:
                print("Aggregator is not ready")
                print("Try it later")
                await self.agent.stop()

            prix = await self.receive(timeout=10)
            if prix.metadata["Prix"] == 'Elec':
                data = prix.body.split(': ')[1]
                self.agent.prixlist = literal_eval(data)
                print(self.agent.prixlist)
            else:
                print("Did not receive the list of price")
                print("Try it later")
                await self.agent.stop()

            vente = await self.receive(timeout=20)
            if vente.metadata["Prix"] == 'Vente':
                data = vente.body.split(': ')[1]
                self.agent.venteprix = literal_eval(data)
                print(self.agent.venteprix)
            else:
                print("Did not receive the list of vente price")
                print("Try it later")
                await self.agent.stop()

        async def on_end(self) -> None:
            self.agent.add_behaviour(self.agent.Initialization())

    class SendData(OneShotBehaviour):
        async def run(self) -> None:
            msg_consommation = Message(to="spade01@jabbim.com")
            msg_consommation.set_metadata("data", "consommation")
            msg_consommation.body = f"{self.agent.name} sent its consommation: " + str(self.agent.consommation)
            await self.send(msg_consommation)

            msg_production = Message(to="spade01@jabbim.com")
            msg_production.set_metadata("data", "production")
            msg_production.body = f"{self.agent.name} sent its production: " + str(self.agent.production)
            await self.send(msg_production)

            msg_c_e = Message(to="spade01@jabbim.com")
            msg_c_e.set_metadata("data", "consommation excess")
            msg_c_e.body = f"{self.agent.name} sent its consommation excess: " + str(self.agent.consommation_excess)
            await self.send(msg_c_e)

            msg_p_e = Message(to="spade01@jabbim.com")
            msg_p_e.set_metadata("data", "production excess")
            msg_p_e.body = f"{self.agent.name} sent its production excess: " + str(self.agent.production_excess)
            await self.send(msg_p_e)

            # Notice the aggregator of finishing sending all datas
            msg_fini = Message(to="spade01@jabbim.com")
            msg_fini.set_metadata("flag", "Done")
            msg_fini.body = f"{self.agent.name} sent all data"
            await self.send(msg_fini)

    class ReceData(CyclicBehaviour):
        async def run(self) -> None:
            msg = await self.receive(timeout=10)
            if msg:
                print(f"{self.agent.name} received {msg.get_metadata('data')} from {str(msg.sender).split('@')[0]}")
                if msg.get_metadata("data") == "consommation":
                    self.agent.c_t = literal_eval(msg.body)
                elif msg.get_metadata("data") == "consommation excess":
                    self.agent.t_con_ex = literal_eval(msg.body)
                elif msg.get_metadata("data") == "production excess":
                    self.agent.t_pro_ex = literal_eval(msg.body)
                elif msg.get_metadata("data") == "production":
                    self.agent.p_t = literal_eval(msg.body)

            else:
                print(f"{self.agent.name} Did not received any message after 10 seconds")
                self.kill()

        async def on_end(self) -> None:
            await self.agent.stop()

    async def setup(self) -> None:
        print(f"{self.name} created.")
        self.consommation = []
        self.production = []
        self.consommation_excess = []  # P charge
        self.production_excess = []  # P discharge
        self.add_behaviour(self.MkConnection())


async def main():
    home1 = Maison("spade02@jabbim.com", "123456")
    await home1.start()
    await spade.wait_until_finished(home1)
    await home1.stop()


if __name__ == "__main__":
    spade.run(main())
