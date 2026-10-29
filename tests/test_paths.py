from costwire import paths


def test_project_folders_exist():
    for folder in (paths.DATA_DIR, paths.SITE_DIR, paths.TESTS_DIR):
        assert folder.is_dir(), folder
