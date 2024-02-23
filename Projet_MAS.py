from agg3_1 import Aggregator
from ver4 import Maison
import spade

num_de_maison = 2  # il faut aussi changer la nombre des maison dans la ficher agg3_1.py


async def main():
    homelist = []
    for i in range(num_de_maison):
        homelist.append(Maison(f"spade0{i+2}@jabbim.com", "123456"))  # il faut changer le jid de la maison
    agg = Aggregator("spade01@jabbim.com", "123456")  # il faut changer le jid de l'aggregator
    await agg.start()
    for home in homelist:
        await home.start()
    await spade.wait_until_finished(agg)
    for home in homelist:
        await spade.wait_until_finished(home)
    await agg.stop()
    for home in homelist:
        await home.stop()

if __name__ == "__main__":
    spade.run(main())
