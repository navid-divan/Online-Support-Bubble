import pytest

from osb.protocol.policy import Policy, attr, validate


def test_satisfied_when_each_clause_has_a_present_attribute():
    p = Policy.of({"cancer_specialist", "medical_doctor"}, {"experience_gt_5y"})
    assert p.is_satisfied_by({"cancer_specialist", "experience_gt_5y"})
    assert p.is_satisfied_by({"medical_doctor", "experience_gt_5y", "legal_advisor"})


def test_not_satisfied_when_a_clause_is_unmet():
    p = Policy.of({"cancer_specialist"}, {"experience_gt_5y"})
    assert not p.is_satisfied_by({"cancer_specialist"})
    assert not p.is_satisfied_by({"experience_gt_5y"})
    assert not p.is_satisfied_by(set())


def test_size_and_attributes():
    p = Policy.of({"cancer_specialist", "medical_doctor"}, {"experience_gt_5y"})
    assert p.size == 2
    assert p.attributes == frozenset({"cancer_specialist", "medical_doctor", "experience_gt_5y"})


def test_attr_unions_advisor_attributes():
    union = attr([{"cancer_specialist"}, {"experience_gt_5y", "cancer_specialist"}])
    assert union == frozenset({"cancer_specialist", "experience_gt_5y"})


def test_validate_accepts_known_attributes():
    validate(Policy.of({"cancer_specialist"}, {"experience_gt_5y"}))


def test_validate_rejects_unknown_attribute():
    with pytest.raises(ValueError):
        validate(Policy.of({"not_a_real_attribute"}))


def test_validate_rejects_empty_policy():
    with pytest.raises(ValueError):
        validate(Policy.of())


def test_validate_rejects_empty_clause():
    with pytest.raises(ValueError):
        validate(Policy(clauses=(frozenset(),)))
