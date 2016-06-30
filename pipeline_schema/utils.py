import os
import json
import base64
import sys
import uuid
import traceback
import re

sys.path.insert(0, r'K:\development\tools\lucidity\source')

import lucidity


def get_ftrack_data(entityId):
    import ftrack

    # if in a connect session, we can get the entityId from the connect event
    if 'FTRACK_CONNECT_EVENT' in os.environ and not entityId:
        decodedEventData = json.loads(
            base64.b64decode(
                os.environ.get('FTRACK_CONNECT_EVENT')
            )
        )

        entityId = decodedEventData['selection'][0]['entityId']

    entity = None

    # resolving the entityId to a ftrack entity
    try:
        entity = ftrack.Task(entityId)
        if entity.getObjectType() != 'Task':
            entity = None
    except:
        pass

    try:
        entity = ftrack.Component(entityId)
    except:
        pass

    if not entity:
        raise ValueError('Ftrack entity type not recognized.')

    parents = entity.getParents()
    project = parents[-1]
    data = dict()

    # project root
    root = project.getRoot()
    if root.endswith('\\'):
        root = root[:-1]
    data['project_root'] = root

    # getting task data
    if entity.get('entityType') == 'task':

        path = []
        asset_build = None
        for parent in parents[:-1]:
            path.append(parent.getName())

            if parent.getObjectType() == 'Asset Build':
                asset_build = parent
        path.reverse()

        try:
            data['parent_path'] = os.path.join(*path)
        except:
            data['parent_path'] = ''

        try:
            data['parent_types'] = parents[-2].getObjectType() + 's'
        except:
            data['parent_types'] = ''

        data['task_name'] = entity.getName()
        data['name'] = entity.getParent().getName()

        # if its an asset
        if asset_build:
            data['asset_type'] = asset_build.getType().getName()
            data['asset_name'] = asset_build.getName()
            data['root'] = project.getRoot()

    # getting component data
    if entity.get('entityType') == 'component':

        asset = entity.getVersion().getAsset()
        data['output_type'] = asset.getType().getShort()

        path = []
        for parent in parents[2:-1]:
            path.append(parent.getName())
        path.reverse()

        data['parent_path'] = os.path.join(*path)
        data['task_name'] = entity.getVersion().getTask().getName()
        data['name'] = entity.getName()

    return data


def get_data(item_id=None):

    data = dict()

    try:
        data = get_ftrack_data(item_id)
    except:
        print traceback.format_exc()

    data['user_directory'] = os.path.expanduser("~")
    data['uuid'] = str(uuid.uuid4())

    # version
    data['version'] = data.get('version', 1)

    return data


def get_path(path_type, data):
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.yml')
    schema = lucidity.Schema.from_yaml(schema_path)

    # required format of version item
    if isinstance(data['version'], int):
        data['version'] = str(data['version']).zfill(3)

    # checking all required data exists
    missing_keys = list(schema[path_type].keys() - set(data.keys()))
    if len(missing_keys) != 0:
        raise ValueError('Missing keys in data: %s' % missing_keys)

    paths = {}
    for fm in schema.format_all(data):
        paths[fm[1].name] = fm[0]

    # removing spaces and backslashes
    result = paths[path_type].replace(' ', '_').replace('\\', '/')

    # removing multiple forward slashes
    result = re.sub("/{2,}", "/", result)

    return result.lower()

if __name__ == "__main__":

    data = get_data()
    print get_path('version', data)
