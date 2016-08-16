import os
import sys
import uuid
import traceback
import re

sys.path.insert(0, r"K:\development\tools\lucidity\source")

import lucidity


def get_ftrack_data(entityId):
    import ftrack
    import base64
    import json

    # if in a connect session, we can get the entityId from the connect event
    if "FTRACK_CONNECT_EVENT" in os.environ and not entityId:
        decodedEventData = json.loads(
            base64.b64decode(
                os.environ.get("FTRACK_CONNECT_EVENT")
            )
        )

        entityId = decodedEventData["selection"][0]["entityId"]

    entity = None

    # resolving the entityId to a ftrack entity
    try:
        entity = ftrack.Task(entityId)
        if entity.getObjectType() != "Task":
            entity = None
    except:
        pass

    try:
        entity = ftrack.Component(entityId)
    except:
        pass

    if not entity:
        raise ValueError("Ftrack entity type not recognized.")

    parents = entity.getParents()
    project = parents[-1]
    data = dict()

    # project root
    root = project.getRoot()
    if root.endswith("\\"):
        root = root[:-1]
    data["project_root"] = root

    # getting task data
    if entity.get("entityType") == "task":

        path = []
        asset_build = None
        for parent in parents[:-1]:
            path.append(parent.getName())

            if parent.getObjectType() == "Asset Build":
                asset_build = parent
        path.reverse()

        try:
            data["parent_path"] = os.path.join(*path)
        except:
            data["parent_path"] = ""

        try:
            data["parent_types"] = parents[-2].getObjectType() + "s"
        except:
            data["parent_types"] = ""

        data["task_name"] = entity.getName()
        data["name"] = entity.getParent().getName()

        # if its an asset
        if asset_build:
            data["asset_type"] = asset_build.getType().getName()
            data["asset_name"] = asset_build.getName()
            data["root"] = project.getRoot()
            data["parent_types"] = ""

            # traverse parents to figure out whether its an
            # episodic/sequence/shot asset. Fallback is project based asset.
            path = ""
            for parent in asset_build.getParents():
                try:
                    if parent.getObjectType() != "Folder":
                        path = os.path.join(parent.getObjectType() + "s",
                                            parent.getName(),
                                            "library",
                                            asset_build.getType().getName(),
                                            asset_build.getName())
                        break
                except:
                    path = os.path.join("library",
                                        asset_build.getType().getName(),
                                        asset_build.getName())

            data["parent_path"] = path

    # getting component data
    if entity.get("entityType") == "component":

        asset = entity.getVersion().getAsset()
        data["output_type"] = asset.getType().getShort()

        path = []
        for parent in parents[2:-1]:
            path.append(parent.getName())
        path.reverse()

        data["parent_path"] = os.path.join(*path)
        data["task_name"] = entity.getVersion().getTask().getName()
        data["name"] = entity.getName()

    # determine schema to use
    schema_path = os.path.join(os.path.dirname(__file__), "schema.yml")
    data["schema_path"] = schema_path

    # excluding certain projects from new schema
    if project.getId() in ["ddf8b7b2-5275-11e6-9cd6-42010af00048",
                           "20010154-1c3f-11e6-89ac-42010af00048",
                           "caa9a7ea-57ff-11e6-ab9e-42010af00048",
                           "7bbf1c8a-b5f5-11e4-980e-040112b6a801",
                           "ad4a7154-29a9-11e6-b514-42010af00048"]:
        schema_path = os.path.join(os.path.dirname(__file__), "schema_old.yml")
        data["schema_path"] = schema_path

    # excluding certain episodes from new schema
    for p in parents:
        if p.getId() in ["f52c8b38-13a1-11e6-a516-42010af00048",
                         "07968dd0-57ec-11e6-a479-42010af00048",
                         "9b9f136c-5341-11e6-ba2b-42010af00048",
                         "a82e8728-2d96-11e6-8df0-42010af00048",
                         "c60b7500-3d25-11e6-a581-42010af00048",
                         "54416bcc-4db1-11e6-b3a4-42010af00048",
                         "cdc1dc54-4e86-11e6-a558-42010af00048"]:
            schema_path = os.path.join(os.path.dirname(__file__),
                                       "schema_old.yml")
            data["schema_path"] = schema_path

    return data


def get_data(item_id=None):

    data = dict()
    schema_path = os.path.join(os.path.dirname(__file__), "schema.yml")
    data["schema_path"] = schema_path

    try:
        data = get_ftrack_data(item_id)
    except:
        print traceback.format_exc()

    data["user_directory"] = os.path.expanduser("~")
    data["uuid"] = str(uuid.uuid4())

    # version
    data["version"] = data.get("version", 1)

    return data


def get_path(path_type, data):
    schema = lucidity.Schema.from_yaml(data["schema_path"])

    # required format of version item
    if isinstance(data["version"], int):
        data["version"] = str(data["version"]).zfill(3)

    # checking all required data exists
    missing_keys = list(schema[path_type].keys() - set(data.keys()))
    if len(missing_keys) != 0:
        raise ValueError("Missing keys in data: %s" % missing_keys)

    paths = {}
    for fm in schema.format_all(data):
        paths[fm[1].name] = fm[0]

    # removing spaces and backslashes
    result = paths[path_type].replace(" ", "_").replace("\\", "/")

    # removing multiple forward slashes
    result = re.sub("/{2,}", "/", result)

    return result.lower()

if __name__ == "__main__":

    data = get_data("0234855c-4f6a-11e6-ba27-42010af00048")
    data["extension"] = "mb"
    print get_path("task_work", data)
