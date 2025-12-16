import pytest

from cgshop2026_pyutils.io import open_file


def test_open_file_reports_missing_path(tmp_path):
    missing_path = tmp_path / "missing.instance.json"

    @open_file
    def read_dummy(f):
        return f.read()

    with pytest.raises(FileNotFoundError) as excinfo:
        read_dummy(missing_path)

    message = str(excinfo.value)
    assert "File not found" in message
    assert str(missing_path.resolve()) in message
