import itertools
from engine.audit import MATRICES, REQUIRED, audit
from engine.ontology import read, write
from engine.matchups import evaluate


def test_all_511_unique_cells_and_reciprocity(knowledge):
    count = 0
    for name, (rd, cd) in MATRICES.items():
        cells = knowledge.matrices[name]["cells"]
        pairs = {(c["row_id"], c["column_id"]) for c in cells}
        assert len(pairs) == len(cells)
        assert pairs == set(itertools.product([rd + "." + i for i in REQUIRED[rd]], [cd + "." + i for i in REQUIRED[cd]]))
        for c in cells:
            assert -1 <= c["edge"] <= 1
            assert c["mechanism"] and c["how"] and c["preconditions"]
            if rd == cd:
                assert c["edge"] == -knowledge.cells[name][c["column_id"], c["row_id"]]["edge"]
        count += len(cells)
    assert count == 511


def test_base_cell_numbers_follow_documented_lane_formula(knowledge):
    for m in knowledge.matrices.values():
        for c in m["cells"]:
            a, b = knowledge.options[c["row_id"]], knowledge.options[c["column_id"]]
            ax, bx = set(a["tactical_conditions"]["answers"]), set(b["tactical_conditions"]["answers"])
            ae, be = set(a["tactical_conditions"]["exposes"]), set(b["tactical_conditions"]["exposes"])
            if m["column_dimension"] in ["target", "kicking"]:
                expected = (len(ax & bx) - len(ae & bx)) / len(bx)
            else:
                expected = (len(ax & be) / len(be) - len(bx & ae) / len(ae)) / 2
            assert c["edge"] == expected


def test_asymmetric_directions_are_both_evaluated(knowledge, cards):
    a, b = cards["maleek"], cards["donnell"]
    ab, ba = evaluate(knowledge, a, b, "mma"), evaluate(knowledge, b, a, "mma")
    for x, y in zip(ab, ba):
        assert x["signed_edge_for_a"] == -y["signed_edge_for_a"]
        rd, cd = MATRICES[x["matrix_id"]]
        assert len(x["directions"]) == (1 if rd == cd else 2)
        if rd != cd:
            assert x["directions"][0] == y["directions"][1]
            assert x["directions"][1] == y["directions"][0]


def test_missing_matrix_reference_is_rejected(project_copy):
    path = project_copy / "data/matchups.json"
    d = read(path)
    d["matrices"][0]["cells"].pop()
    write(path, d)
    assert audit(project_copy)["status"] == "FAIL"
