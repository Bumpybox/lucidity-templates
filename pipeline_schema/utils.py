import os

import lucidity


def get_ftrack_data(entityId):
    import ftrack

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
        data['asset_type'] = asset_build.getType().getName().lower()
        data['asset_name'] = asset_build.getName().lower()
        data['root'] = project.getRoot()

    return data


def get_path(path_type, data, version, extension):
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.yml')
    schema = lucidity.Schema.from_yaml(schema_path)

    # non ftrack data
    data['version'] = version
    data['filetype'] = extension

    paths = {}
    for fm in schema.format_all(data):
        paths[fm[1].name] = fm[0]

    return paths[path_type].replace('\\', '/')

if __name__ == "__main__":
    data = get_ftrack_data('06499796-1e77-11e6-a1d5-42010af00048')
    version = str(1).zfill(3)
    extension = 'scn'
    print get_path('task_work', data, version, extension)
