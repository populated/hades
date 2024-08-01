from hades.managers.updater import Updater
from hades.hades import Hades
import json

config = json.load(open("config.json", "r"))
update = json.load(open("update.json", "r"))

Updater(current_version=update["version"]).run()
Hades().run(token=config["token"])
