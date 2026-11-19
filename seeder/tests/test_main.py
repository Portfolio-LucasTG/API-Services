from iris_seeder.__main__ import main


def test_main_returns_success() -> None:
    assert main() == 0
