from random import randint
from ast import literal_eval
import matplotlib.pyplot as plt

import spade
from spade.agent import Agent
from spade.message import Message
from spade.behaviour import CyclicBehaviour, OneShotBehaviour

from devices import devices

path = f"D:/Users/shiguang/Documents/Stage202309_SHI_Guangyu/data_stage/"
jid_agg = "spade01@jabbim.com"


class Maison(Agent):
    c_t = [0] * 24
    p_t = [0] * 24
    QC = [0] * 24

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
                    self.agent.production.append(randint(2, 5))

            self.agent.st = randint(7, 17)
            self.agent.lt = randint(self.agent.st + 1, 18)
            self.agent.battery, self.agent.ev = devices(consommation=self.agent.consommation,
                                                        production=self.agent.production,
                                                        prixElec=self.agent.prixlist, prixVente=self.agent.venteprix,
                                                        starttime=self.agent.st, leavetime=self.agent.lt)

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
            # plt.show()

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
            # plt.show()

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
            # plt.show()

            # consommation excess & production excess
            for t in range(24):
                diff = self.agent.production[t] - self.agent.consommation[t] - self.agent.ev.Pchar[t]
                if diff < 0:
                    self.agent.consommation_excess.append(round(abs(diff) - self.agent.battery.Pdis[t], 2))
                    self.agent.production_excess.append(0)
                    self.agent.identity.append(0)
                else:
                    self.agent.consommation_excess.append(0)
                    self.agent.production_excess.append(round(diff - self.agent.battery.Pchar[t], 2))
                    self.agent.identity.append(1)

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
            # plt.show()

        async def on_end(self) -> None:
            self.agent.add_behaviour(self.agent.savedata(self.agent.prixlist, self.agent.venteprix,
                                                         self.agent.consommation, self.agent.production,
                                                         self.agent.battery, self.agent.ev,
                                                         self.agent.consommation_excess, self.agent.production_excess))
            self.agent.add_behaviour(self.agent.senddata("profil"))
            self.agent.add_behaviour(self.agent.ReceData())

    def savedata(self, prixlist=None, venteprix=None, consommation=None, production=None, battery=None, EV=None,
                 CS=None, PS=None, QR=None, QC=None):
        class SaveData(OneShotBehaviour):
            async def run(self) -> None:
                import pandas as pd
                import os.path
                if not QR:
                    data_profil = pd.DataFrame([prixlist, venteprix, consommation, production,
                                                battery.SoC, battery.Pchar, battery.Pdis, EV.SoC, EV.Pchar, CS, PS],
                                               index=["buy price", "sell price",
                                                      "consumption", "production",
                                                      "battery SoC", "Power charge", "Power discharge",
                                                      "EV SoC", "Power charge",
                                                      "Consumption excess", "¨Production excess"],
                                               columns=range(24))
                else:
                    data_profil = pd.DataFrame([QC, battery.SoC, battery.Pchar_ex, battery.Pdis, EV.SoC, EV.Pchar_ex, QR],
                                               index=["QC", "battery SoC", "Power charge ex", "Power discharge",
                                                      "EV SoC", "Power charge_ex", "QR"],
                                               columns=range(24))
                path_data = path + f"{self.agent.name}.xlsx"
                if os.path.isfile(path_data):
                    with pd.ExcelWriter(path_data, mode="a", if_sheet_exists='new') as writer:
                        data_profil.to_excel(writer)
                else:
                    data_profil.to_excel(path_data, float_format="%.2f")

        return SaveData()

    class MkConnection(OneShotBehaviour):
        async def run(self) -> None:
            msg = Message(to=jid_agg)
            msg.body = "Is Aggregator here ?"
            await self.send(msg)
            print("Making Connection")
            rep = await self.receive(timeout=60)
            if rep:
                print(rep.body)
                print("Connected")
            else:
                print("Aggregator is not ready")
                print("Try it later")
                await self.agent.stop()

            prix = await self.receive(timeout=60)
            if prix.metadata["Prix"] == 'Elec':
                data = prix.body.split(': ')[1]
                self.agent.prixlist = literal_eval(data)
                print(self.agent.prixlist)
            else:
                print("Did not receive the list of price")
                print("Try it later")
                await self.agent.stop()

            vente = await self.receive(timeout=60)
            if vente.metadata["Prix"] == 'Vente':
                data = vente.body.split(': ')[1]
                self.agent.venteprix = literal_eval(data)
                print(self.agent.venteprix)
            else:
                print("Did not receive the list of vente price")
                print("Try it later")
                await self.agent.stop()

            start = await self.receive(timeout=60)
            if start.metadata["flag"] == "start":
                print("Tous les maisons sont prêtes")
                self.agent.add_behaviour(self.agent.Initialization())

    def senddata(self, contenu: str):
        class SendData(OneShotBehaviour):
            async def run(self) -> None:
                if contenu == "profil":
                    msg_consommation = Message(to=jid_agg)
                    msg_consommation.set_metadata("data", "consommation")
                    msg_consommation.body = f"{self.agent.name} sent its consommation: " + str(self.agent.consommation)
                    await self.send(msg_consommation)

                    msg_production = Message(to=jid_agg)
                    msg_production.set_metadata("data", "production")
                    msg_production.body = f"{self.agent.name} sent its production: " + str(self.agent.production)
                    await self.send(msg_production)

                    msg_c_e = Message(to=jid_agg)
                    msg_c_e.set_metadata("data", "consommation excess")
                    msg_c_e.body = f"{self.agent.name} sent its consommation excess: " + str(
                        self.agent.consommation_excess)
                    await self.send(msg_c_e)

                    msg_p_e = Message(to=jid_agg)
                    msg_p_e.set_metadata("data", "production excess")
                    msg_p_e.body = f"{self.agent.name} sent its production excess: " + str(self.agent.production_excess)
                    await self.send(msg_p_e)

                    # Notice the aggregator of finishing sending all datas
                    msg_fini = Message(to=jid_agg)
                    msg_fini.set_metadata("flag", "Profil done")
                    msg_fini.body = f"{self.agent.name} sent all data"
                    await self.send(msg_fini)
                elif contenu == "QR":
                    msg_QR = Message(to=jid_agg)
                    msg_QR.set_metadata("data", "QR")
                    msg_QR.body = f"{self.agent.name} sent its QR: " + str(self.agent.QR)
                    await self.send(msg_QR)
                    self.agent.QC = [0] * 24
                    self.agent.QR = [0] * 24
                    self.agent.mode = [0] * 24

                    msg_fini = Message(to=jid_agg)
                    msg_fini.set_metadata("flag", "QR done")
                    msg_fini.body = f"{self.agent.name} sent all its QR"
                    await self.send(msg_fini)

        return SendData()

    class ReceData(CyclicBehaviour):
        async def run(self) -> None:
            msg = await self.receive(timeout=20)
            if msg:
                if msg.get_metadata("data") == "QC":
                    print(f"{self.agent.name} received {msg.get_metadata('data')} from {str(msg.sender).split('@')[0]}")
                    self.mode[literal_eval(msg.body.split('|')[2])] = literal_eval(msg.body.split("|")[1])
                    self.agent.QC[literal_eval(msg.body.split('|')[2])] = literal_eval(msg.body.split("|")[0])
                if msg.get_metadata("flag") == "QC done":
                    self.agent.add_behaviour(self.agent.distribution(self.mode))
            else:
                print(f"{self.agent.name} Did not received any message after 10 seconds")
                self.kill()

        async def on_start(self) -> None:
            self.mode = [0] * 24

        async def on_end(self) -> None:
            await self.agent.stop()

    def distribution(self, mode):
        class Distribution(OneShotBehaviour):
            async def run(self) -> None:
                self.agent.battery, self.agent.ev, self.agent.QR = devices(self.agent.prixlist, self.agent.venteprix,
                                                                           self.agent.st, self.agent.lt,
                                                                           QC=self.agent.QC, Bat=self.agent.battery,
                                                                           EV=self.agent.ev, mode=mode)
                self.agent.add_behaviour(self.agent.savedata(QC=self.agent.QC, battery=self.agent.battery, EV=self.agent.ev,
                                                             QR=self.agent.QR))
                self.agent.add_behaviour(self.agent.senddata("QR"))
        return Distribution()

    async def setup(self) -> None:
        print(f"{self.name} created.")
        self.consommation = []
        self.production = []
        self.consommation_excess = []  # P charge
        self.production_excess = []  # P discharge
        self.identity = []  # identity "1" : producteur
        self.add_behaviour(self.MkConnection())


async def main():
    home1 = Maison("spade02@jabbim.com", "123456")
    await home1.start()
    await spade.wait_until_finished(home1)
    await home1.stop()


if __name__ == "__main__":
    spade.run(main())
