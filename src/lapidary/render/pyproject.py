from .config import Config


def mk_pyproject_toml(
    title: str,
    config: Config,
) -> dict:
    return {
        'build-system': {'build-backend': 'poetry.core.masonry.api', 'requires': ['poetry-core>=2']},
        'project': {
            'authors': [],
            'dependencies': [
                'lapidary~=0.12.0',
            ],
            'description': f'Client library for {title}',
            'license': '',
            'name': config.package,
            'requires-python': '~=3.9',
            'version': '0.1.0',
        },
        'tool': {
            'lapidary': config.model_dump(mode='json', exclude_unset=True, exclude_defaults=True),
        },
    }
