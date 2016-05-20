import os

import lucidity
import ftrack


def get_ftrack_data(entityId):

    entity = None
    try:
        entity = ftrack.Task(entityId)
        if entity.getObjectType() != 'Task':
            entity = None
    except:
        pass

    if not entity:
        raise ValueError('Ftrack entity type not recognized.')

    parents = entity.getParents()
    project = parents[-1]

    path = []
    asset_build = None
    for parent in parents[:-1]:
        path.append(parent.getName())

        if parent.getObjectType() == 'Asset Build':
            asset_build = parent

    if len(parents) > 1:
        path.append(parents[-2].getObjectType().lower() + 's')

    path.append(project.getRoot())
    path.reverse()
    root = os.path.join(*path).lower()

    data = {'name': entity.getParent().getName().lower(),
            'task_name': entity.getName().lower(),
            'root': root}

    # if its an asset
    if asset_build:
        print asset_build
        data['asset_type'] = asset_build.getType().getName().lower()
        data['asset_name'] = asset_build.getName().lower()
        data['root'] = project.getRoot()

    # non ftrack data
    data['version'] = str(1).zfill(3)
    data['filetype'] = 'scn'

    return data


def get_path(path_type, data):
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.yml')
    schema = lucidity.Schema.from_yaml(schema_path)

    paths = {}
    for fm in schema.format_all(data):
        paths[fm[1].name] = fm[0]

    return paths[path_type]

data = get_ftrack_data('c1823cac-3057-11e5-8cd9-040112b6a801')
print get_path('task_publish', data)
