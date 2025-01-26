from .config import Config


def mk_pyproject_toml(
    title: str,
    config: Config,
) -> dict:
    return {
        'build-system': {'build-backend': 'poetry.core.masonry.api', 'requires': ['poetry-core>=1.3.2']},
        'tool': {
            'poetry': dict(
                name=config.package,
                description=f'Client library for {title}',
                version='0.1.0',
                authors=[],
                license='',
                packages=[
                    {
                        'include': config.package,
                        'from': 'gen',
                    }
                ],
                dependencies={
                    'python': '3.9',
                    'lapidary': '^0.12.0',
                },
            ),
            'lapidary': config.model_dump(mode='json', exclude_unset=True, exclude_defaults=True),
        },
    }
