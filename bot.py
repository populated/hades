from hades.managers.updater import Updater
from hades.hades import Hades
import json

config = json.load(open("config.json", "r"))

Updater(current_version=2.9).run()
Hades().run(token=config["token"])
