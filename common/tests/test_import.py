from importlib.resources import files

import iris_common


def test_package_imports() -> None:
    assert iris_common.__doc__


def test_package_is_typed() -> None:
    assert files(iris_common).joinpath("py.typed").is_file()
