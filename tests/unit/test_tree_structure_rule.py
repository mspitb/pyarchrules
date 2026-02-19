"""Tests for TreeStructureRule."""

from pyarchrules.core.rules.linter.tree_rule import TreeRule


class TestTreeStructureRule:
    def test_no_tree_spec_passes(self, make_service_spec):
        assert len(TreeRule(make_service_spec()).validate()) == 0

    def test_all_paths_present_passes(self, make_service_spec, tmp_test_dir, monkeypatch):
        monkeypatch.chdir(tmp_test_dir)
        (tmp_test_dir / "api").mkdir()
        (tmp_test_dir / "domain").mkdir()
        (tmp_test_dir / "infra").mkdir()

        spec = make_service_spec(tree=["api", "domain", "infra"])
        assert len(TreeRule(spec).validate()) == 0

    def test_missing_paths_returns_error(self, make_service_spec, tmp_test_dir, monkeypatch):
        monkeypatch.chdir(tmp_test_dir)
        (tmp_test_dir / "api").mkdir()
        (tmp_test_dir / "domain").mkdir()

        spec = make_service_spec(tree=["api", "domain", "tests"])
        violations = TreeRule(spec).validate()

        assert len(violations) == 1
        assert violations[0].severity == "error"
        assert "tests" in violations[0].details["missing_paths"]

    def test_nested_paths_validation(self, make_service_spec, tmp_test_dir, monkeypatch):
        monkeypatch.chdir(tmp_test_dir)
        (tmp_test_dir / "api" / "v1").mkdir(parents=True)
        (tmp_test_dir / "api" / "v2").mkdir()

        spec = make_service_spec(tree=["api", "api/v1", "api/v2"])
        assert len(TreeRule(spec).validate()) == 0

    def test_missing_nested_path_returns_error(self, make_service_spec, tmp_test_dir, monkeypatch):
        monkeypatch.chdir(tmp_test_dir)
        (tmp_test_dir / "api" / "v1").mkdir(parents=True)

        spec = make_service_spec(tree=["api", "api/v1", "api/v2"])
        violations = TreeRule(spec).validate()

        assert len(violations) == 1
        assert "api/v2" in violations[0].details["missing_paths"]

    def test_tree_strict_detects_extra_items(self, make_service_spec, tmp_test_dir, monkeypatch):
        monkeypatch.chdir(tmp_test_dir)
        api_dir = tmp_test_dir / "api"
        api_dir.mkdir()
        (api_dir / "v1").mkdir()
        (api_dir / "v2").mkdir()
        (api_dir / "extra_file.txt").touch()

        spec = make_service_spec(tree=["api", "api/v1"], tree_strict=True)
        violations = TreeRule(spec).validate()

        warnings = [v for v in violations if v.severity == "warning"]
        assert len(warnings) == 1
        assert "v2" in warnings[0].details["extra_items"]
        assert "extra_file.txt" not in warnings[0].details["extra_items"]

    def test_tree_strict_false_allows_extra_items(
        self, make_service_spec, tmp_test_dir, monkeypatch
    ):
        monkeypatch.chdir(tmp_test_dir)
        api_dir = tmp_test_dir / "api"
        api_dir.mkdir()
        (api_dir / "v1").mkdir()
        (api_dir / "extra").mkdir()

        spec = make_service_spec(tree=["api", "api/v1"], tree_strict=False)
        assert len(TreeRule(spec).validate()) == 0

    def test_tree_allow_files_allows_files_but_not_folders(
        self, make_service_spec, tmp_test_dir, monkeypatch
    ):
        monkeypatch.chdir(tmp_test_dir)
        api_dir = tmp_test_dir / "api"
        api_dir.mkdir()
        (api_dir / "v1").mkdir()
        (api_dir / "extra_folder").mkdir()
        (api_dir / "readme.txt").touch()
        (api_dir / "config.json").touch()

        spec = make_service_spec(tree=["api", "api/v1"], tree_strict=True, tree_allow_files=True)
        violations = TreeRule(spec).validate()

        warnings = [v for v in violations if v.severity == "warning"]
        assert len(warnings) == 1
        assert "extra_folder" in warnings[0].details["extra_items"]
        assert "readme.txt" not in str(warnings[0].details["extra_items"])

    def test_tree_allow_files_false_detects_both_files_and_folders(
        self, make_service_spec, tmp_test_dir, monkeypatch
    ):
        monkeypatch.chdir(tmp_test_dir)
        api_dir = tmp_test_dir / "api"
        api_dir.mkdir()
        (api_dir / "v1").mkdir()
        (api_dir / "extra_folder").mkdir()
        (api_dir / "readme.txt").touch()

        spec = make_service_spec(tree=["api", "api/v1"], tree_strict=True, tree_allow_files=False)
        violations = TreeRule(spec).validate()

        warnings = [v for v in violations if v.severity == "warning"]
        assert len(warnings) == 1
        assert "extra_folder" in warnings[0].details["extra_items"]
        assert "readme.txt" in warnings[0].details["extra_items"]

    def test_tree_allow_files_default_true(self, make_service_spec, tmp_test_dir, monkeypatch):
        monkeypatch.chdir(tmp_test_dir)
        api_dir = tmp_test_dir / "api"
        api_dir.mkdir()
        (api_dir / "v1").mkdir()
        (api_dir / "file.txt").touch()

        spec = make_service_spec(tree=["api", "api/v1"], tree_strict=True)
        assert len([v for v in TreeRule(spec).validate() if v.severity == "warning"]) == 0

    def test_service_directory_not_exists_returns_error(self, make_service_spec):
        spec = make_service_spec(path="nonexistent", tree=["api"])
        violations = TreeRule(spec).validate()

        assert len(violations) == 1
        assert violations[0].severity == "error"
        assert "does not exist" in violations[0].message

    def test_empty_tree_list_passes(self, make_service_spec):
        assert len(TreeRule(make_service_spec(tree=[])).validate()) == 0

    def test_single_path_validation(self, make_service_spec, tmp_test_dir, monkeypatch):
        monkeypatch.chdir(tmp_test_dir)
        (tmp_test_dir / "api").mkdir()
        spec = make_service_spec(tree=["api"])
        assert len(TreeRule(spec).validate()) == 0

    def test_rule_name_property(self, make_service_spec):
        assert TreeRule(make_service_spec()).rule_name == "tree_structure"
