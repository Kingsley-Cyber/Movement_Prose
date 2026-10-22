import copy
from pathlib import Path
import pytest
from engine.ontology import Knowledge, ROOT, read


@pytest.fixture(scope="session")
def knowledge():
    return Knowledge()


@pytest.fixture
def cards(knowledge):
    return {p.stem: knowledge.card(p) for p in sorted((ROOT / "cards").glob("*.json"))}


@pytest.fixture
def fight(cards, knowledge):
    from engine.fight_director import plan
    return plan(cards["maleek"], cards["donnell"], seed=42, knowledge=knowledge)


@pytest.fixture
def project_copy(tmp_path):
    import shutil
    target = tmp_path / "project"
    shutil.copytree(ROOT, target, ignore=shutil.ignore_patterns(".venv", "__pycache__", ".pytest_cache", "outputs", "reports"))
    return target
