from varenrich.download import download_file


def test_download_file_uses_partial_then_atomic_replace(tmp_path):
    source = tmp_path / "source.txt"
    source.write_text("public annotation\n")
    destination = tmp_path / "downloaded.txt"
    assert download_file(source.as_uri(), destination) == destination
    assert destination.read_text() == "public annotation\n"
    assert not destination.with_suffix(".txt.partial").exists()
