import spade
from spade.agent import Agent
from spade.message import Message
from spade.behaviour import OneShotBehaviour, CyclicBehaviour
from ast import literal_eval

num_maison = 2


class Aggregator(Agent):
    c_t = [0] * 24
    p_t = [0] * 24
    t_con_ex = [0] * 24
    t_pro_ex = [0] * 24
    QR = [0] * 24
    mode = [0] * 24
    consommateur: list[list[str]] = [[] for i in range(24)]
    homelist = []
    prixlist = []  # ¢/kWh
    venteprix = []  # ¢/kWh

    class PrixInit(OneShotBehaviour):  # Time-of-use(TOU) rates
        async def run(self) -> None:
            for t in range(24):
                if t <= 7 or t > 19:
                    self.agent.prixlist.append(8.7)
                    self.agent.venteprix.append(round(8.7 * 0.9, 1))
                elif 11 < t <= 17:
                    self.agent.prixlist.append(12.2)
                    self.agent.venteprix.append(round(12.2 * 0.9, 1))
                else:
                    self.agent.prixlist.append(18.2)
                    self.agent.venteprix.append(round(18.2 * 0.9, 1))
            print("The price is ready")

        async def on_end(self) -> None:
            self.agent.add_behaviour(self.agent.MkConnection())

    class MkConnection(CyclicBehaviour):
        async def run(self) -> None:
            msg = await self.receive(timeout=30)
            if msg:
                if msg.body == "Is Aggregator here ?":
                    print(f"{str(msg.sender).split('@')[0]} connected")
                    self.agent.homelist.append(str(msg.sender))
                    rep = Message(to=f"{msg.sender}")
                    rep.body = "Yes. Aggregator is ready, please send data."
                    await self.send(rep)

                    # Send the price of electricity
                    prix = Message(to=f"{msg.sender}")
                    prix.set_metadata("Prix", "Elec")
                    prix.body = "The price of the electricity is: " + str(self.agent.prixlist)
                    await self.send(prix)

                    # Send the price of selling electricity
                    vente = Message(to=f"{msg.sender}")
                    vente.set_metadata("Prix", "Vente")
                    vente.body = "The price of the vente is: " + str(self.agent.venteprix)
                    await self.send(vente)

                    self.count += 1
                    if self.count == num_maison:
                        print("Tous les maison connected.")
                        for home in self.agent.homelist:
                            msg_start = Message(to=home)
                            msg_start.set_metadata("flag", "start")
                            msg_start.body = "Tous les maison connected. Please send datas."
                            await self.send(msg_start)
                        self.kill()
                    print(f"Il reste {num_maison - self.count} maisons à connecter.")

        async def on_start(self) -> None:
            self.count = 0

        async def on_end(self) -> None:
            self.agent.add_behaviour(self.agent.ReceData())

    class ReceData(CyclicBehaviour):
        async def run(self) -> None:
            msg = await self.receive(timeout=30)
            if msg:
                # When receiving all datas from a home
                if msg.get_metadata("flag") == "Profil done":
                    self.count += 1
                    print(f"{str(msg.sender).split('/')[0]} sent all data")
                    self.num_consommateur = max([len(l) for l in self.agent.consommateur])
                    if self.count == len(self.agent.homelist):
                        print("All home finished sending data.")
                        if self.num_consommateur != 0:
                            print(f"Le {self.iteration}ère iteration")
                            self.iteration += 1
                            self.agent.add_behaviour(self.agent.distribution())
                            self.num_consommateur = max([len(l) for l in self.agent.consommateur])
                            self.count = 0
                        else:
                            print("No more consommateur")
                            self.kill()

                elif msg.get_metadata("flag") == "QR done":
                    self.count += 1
                    print(f"{str(msg.sender).split('/')[0]} sent its QR")
                    if self.count == self.num_consommateur:
                        self.count = 0
                        print("All consommateurs sent its QR")
                        print(f"QR : {self.agent.QR}")
                        self.num_consommateur = max([len(l) for l in self.agent.consommateur])
                        if self.num_consommateur == 0:
                            print("No more consommateur.")
                            self.kill()
                        else:
                            print(f"Le {self.iteration}ère iteration")
                            self.iteration += 1
                            self.agent.add_behaviour(self.agent.distribution(self.agent.QR))
                            self.agent.QR = [0] * 24

                # When receiving datas from a home
                else:
                    data = msg.body.split(": ")[1]
                    if msg.get_metadata("data") == "consommation":
                        self.agent.c_t = [self.agent.c_t[t] + literal_eval(data)[t] for t in range(24)]
                        print(
                            f"{self.agent.name} received {msg.get_metadata('data')} from {str(msg.sender).split('@')[0]}")
                    elif msg.get_metadata("data") == "production":
                        self.agent.p_t = [self.agent.p_t[t] + literal_eval(data)[t] for t in range(24)]
                        print(
                            f"{self.agent.name} received {msg.get_metadata('data')} from {str(msg.sender).split('@')[0]}")

                    elif msg.get_metadata("data") == "consommation excess":
                        self.agent.t_con_ex = [self.agent.t_con_ex[t] + literal_eval(data)[t] for t in range(24)]
                        print(
                            f"{self.agent.name} received {msg.get_metadata('data')} from {str(msg.sender).split('@')[0]}")
                    elif msg.get_metadata("data") == "production excess":
                        self.agent.t_pro_ex = [self.agent.t_pro_ex[t] + literal_eval(data)[t] for t in range(24)]
                        print(
                            f"{self.agent.name} received {msg.get_metadata('data')} from {str(msg.sender).split('@')[0]}")
                        for t in range(24):
                            if literal_eval(data)[t] == 0:
                                self.agent.consommateur[t].append(f"{str(msg.sender)}")
                    elif msg.get_metadata("data") == "QR":
                        for t in range(24):
                            if literal_eval(data)[t] > 0:
                                try:
                                    self.agent.consommateur[t].remove(f"{str(msg.sender)}")
                                except ValueError:
                                    pass
                                self.agent.QR[t] += literal_eval(data)[t]
                                print(f"{self.agent.name} received {msg.get_metadata('data')}: {literal_eval(data)[t]} "
                                      f"at {t}h from {str(msg.sender).split('@')[0]}, so it isn't consommateur any more")
            else:
                print(f"{self.agent.name} did not received any message after 30 seconds")
                self.kill()

        async def on_start(self) -> None:
            self.count = 0
            self.num_consommateur = 0
            self.iteration = 1

        async def on_end(self) -> None:
            await self.agent.stop()

    def distribution(self, QR=None):
        class Distribution(OneShotBehaviour):
            async def run(self) -> None:
                self.agent.distri_tot = [0] * 24
                self.agent.distri_uni = [0] * 24
                l = []
                for t in range(24):
                    if len(self.agent.consommateur[t]) != 0:
                        if not QR:
                            if self.agent.t_pro_ex[t] >= self.agent.t_con_ex[t]:
                                self.agent.distri_tot[t] = self.agent.t_pro_ex[t] - self.agent.t_con_ex[t]
                                self.agent.distri_uni[t] = self.agent.distri_tot[t] / len(self.agent.consommateur[t])
                                self.agent.mode[t] = 1

                            else:
                                self.agent.distri_tot[t] = self.agent.t_pro_ex[t]
                                self.agent.distri_uni[t] = self.agent.distri_tot[t] / len(self.agent.consommateur[t])
                                self.agent.mode[t] = 0
                        else:
                            if QR[t] > 0:
                                self.agent.distri_tot[t] = self.agent.QR[t]
                                self.agent.distri_uni[t] = self.agent.distri_uni[t] / len(self.agent.consommateur[t])
                                if self.agent.t_pro_ex[t] >= self.agent.t_con_ex[t]:
                                    self.agent.mode[t] = 1
                                else:
                                    self.agent.mode[t] = 0
                            else:
                                l.append(t)
                self.agent.add_behaviour(self.agent.senddata(l))

        return Distribution()

    def senddata(self, list_t=None):
        class SendData(OneShotBehaviour):
            async def run(self) -> None:
                consommateur_tot = []

                for t in range(24):
                    for home in self.agent.consommateur[t]:
                        msg_QC = Message(to=home)
                        msg_QC.body = f"{self.agent.distri_uni[t]}" + "|" + f"{self.agent.mode[t]}" + "|" + f"{t}"  # energies a distribute | mode | time
                        msg_QC.set_metadata("data", "QC")
                        await self.send(msg_QC)
                        if home not in consommateur_tot:
                            consommateur_tot.append(home)

                    if t == 23:
                        for home in consommateur_tot:
                            msg_fini = Message(to=home)
                            msg_fini.body = "done"
                            msg_fini.set_metadata("flag", "QC done")
                            await self.send(msg_fini)
                for t in list_t:
                    print(f"No more QR at {t}h")
                    self.agent.consommateur[t].clear()


        return SendData()

    async def setup(self) -> None:
        print(f"{self.name} created")
        self.add_behaviour(self.PrixInit())


async def main():
    agg = Aggregator("spade01@jabbim.com", "123456")
    await agg.start()
    await spade.wait_until_finished(agg)
    await agg.stop()


if __name__ == "__main__":
    spade.run(main())
