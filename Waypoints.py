import json
import os
from dataclasses import dataclass


DATA_DIR = './data'


@dataclass(frozen=True)
class RouteInfo:
    name: str
    valid: bool
    missing: tuple
    error: str | None = None


class Waypoints:
    """ Handles waypoint logic """
    def __init__(self, name) -> None:
        self.name = name

    def select_json(self):
        with open(os.path.join(DATA_DIR, self.name), encoding='utf-8') as file:
            loaded_json = json.load(file)
        loaded_json = loaded_json['waypoints']
        print(f"Initialized script with {len(loaded_json)} nodes")

        return loaded_json


def list_routes(data_dir=DATA_DIR):
    """ Every route file in data/ with whether all of its mark images exist """
    routes = []
    for name in sorted(os.listdir(data_dir)):
        if not name.endswith('.json'):
            continue
        try:
            with open(os.path.join(data_dir, name), encoding='utf-8') as file:
                marks = json.load(file)['waypoints']
        except (OSError, ValueError, KeyError, TypeError) as error:
            routes.append(RouteInfo(name, False, (), f"cannot read route: {error}"))
            continue
        if not isinstance(marks, list) or not marks:
            routes.append(RouteInfo(name, False, (), 'route has no waypoints'))
            continue
        missing = tuple(m for m in marks if not os.path.isfile(m))
        routes.append(RouteInfo(name, not missing, missing))
    return routes


# List of available icons

# 'images/marks/bagmark.png'
# 'images/marks/blueflagmark.png'
# 'images/marks/checkmark.png'
# 'images/marks/crossmark.png'
# 'images/marks/dollarmark.png'
# 'images/marks/exlamationmark.png'
# 'images/marks/knotdown.png'
# 'images/marks/knotup.png'
# 'images/marks/lipsmark.png'
# 'images/marks/lockermark.png'
# 'images/marks/pencilmark.png'
# 'images/marks/pointerdown.png'
# 'images/marks/pointerleft.png'
# 'images/marks/pointerright.png'
# 'images/marks/pointerup.png'
# 'images/marks/questionmark.png'
# 'images/marks/redcrossmark.png'
# 'images/marks/starkmark.png'
# 'images/marks/swordmark.png'
