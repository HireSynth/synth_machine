import json


def json_file_loader(path: str):
    with open(path, "r") as fixture:
        return json.load(fixture)
