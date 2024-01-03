import spade
from spade.agent import Agent
from spade.message import Message
from spade.behaviour import OneShotBehaviour, CyclicBehaviour
from ast import literal_eval


class Aggregator(Agent):
    c_t = [0] * 24
    p_t = [0] * 24
    t_con_ex = [0] * 24
    t_pro_ex = [0] * 24
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
            self.agent.add_behaviour(self.agent.ReceData())

    class ReceData(CyclicBehaviour):
        async def run(self) -> None:
            msg = await self.receive(timeout=30)
            if msg:
                # When receiving demand of connection from a home
                if msg.body == "Is Aggregator here ?":
                    self.agent.homelist.append(str(msg.sender).split('/')[0])
                    self.numhome += 1
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

                # When receiving all datas from a home
                elif msg.get_metadata("flag"):
                    self.count += 1
                    print(f"{str(msg.sender).split('/')[0]} sent all data")
                    if self.count == self.numhome:
                        print("All home finished sending data.")
                        self.agent.add_behaviour(self.agent.SendData())
                    else:
                        pass

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
            else:
                print(f"{self.agent.name} did not received any message after 10 seconds")
                self.kill()

        async def on_start(self) -> None:
            self.count = 0
            self.numhome = 0

        async def on_end(self) -> None:
            await self.agent.stop()

    class SendData(OneShotBehaviour):
        async def run(self) -> None:
            for home in self.agent.homelist:
                msg_con = Message(to=home)
                msg_con.set_metadata("data", "consommation")
                msg_con.body = str(self.agent.c_t)
                await self.send(msg_con)

                msg_pro = Message(to=home)
                msg_pro.set_metadata("data", "production")
                msg_pro.body = str(self.agent.p_t)
                await self.send(msg_pro)

                msg_t_con_ex = Message(to=home)
                msg_t_con_ex.set_metadata("data", "consommation excess")
                msg_t_con_ex.body = str(self.agent.t_con_ex)
                await self.send(msg_t_con_ex)

                msg_t_pro_ex = Message(to=home)
                msg_t_pro_ex.set_metadata("data", "production excess")
                msg_t_pro_ex.body = str(self.agent.t_pro_ex)
                await self.send(msg_t_pro_ex)

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
