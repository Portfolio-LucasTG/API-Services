from importlib.resources import files

import iris_seeder


def test_package_imports() -> None:
    assert iris_seeder.__doc__


def test_package_is_typed() -> None:
    assert files(iris_seeder).joinpath("py.typed").is_file()
