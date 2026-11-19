from importlib.resources import files

import iris_api


def test_package_imports() -> None:
    assert iris_api.__doc__


def test_package_is_typed() -> None:
    assert files(iris_api).joinpath("py.typed").is_file()
