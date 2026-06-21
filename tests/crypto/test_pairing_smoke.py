from osb.config import params
from osb.crypto.primitives import pairing as P


def test_backend_matches_declared_curve():
    assert P.ORDER == params.SCALAR_FIELD_ORDER
    assert P.ORDER.bit_length() == 255


def test_generators_are_non_trivial():
    assert not P.g1_is_identity(P.g1_generator())
    assert not P.g2_is_identity(P.g2_generator())


def test_scalar_inverse():
    x = P.rand_scalar()
    assert (x * P.inv_scalar(x)) % P.ORDER == 1


def test_group_law_g1():
    a, b = P.rand_scalar(), P.rand_scalar()
    lhs = P.g1_mul(P.g1_generator(), (a + b) % P.ORDER)
    rhs = P.g1_add(P.g1_mul(P.g1_generator(), a), P.g1_mul(P.g1_generator(), b))
    assert P.g1_eq(lhs, rhs)


def test_group_law_g2():
    a, b = P.rand_scalar(), P.rand_scalar()
    lhs = P.g2_mul(P.g2_generator(), (a + b) % P.ORDER)
    rhs = P.g2_add(P.g2_mul(P.g2_generator(), a), P.g2_mul(P.g2_generator(), b))
    assert P.g2_eq(lhs, rhs)


def test_identity_and_negation():
    g = P.g1_generator()
    assert P.g1_is_identity(P.g1_add(g, P.g1_neg(g)))
    assert P.g1_eq(P.g1_mul(g, 0), P.g1_identity())


def test_pairing_bilinearity():
    a, b = P.rand_scalar(), P.rand_scalar()
    g1, g2 = P.g1_generator(), P.g2_generator()
    base = P.pair(g1, g2)
    lhs = P.pair(P.g1_mul(g1, a), P.g2_mul(g2, b))
    rhs = P.gt_pow(base, (a * b) % P.ORDER)
    assert P.gt_eq(lhs, rhs)


def test_pairing_non_degenerate():
    base = P.pair(P.g1_generator(), P.g2_generator())
    assert not P.gt_eq(base, P.gt_one())


def test_pairing_linear_in_each_argument():
    a = P.rand_scalar()
    g1, g2 = P.g1_generator(), P.g2_generator()
    base = P.pair(g1, g2)
    assert P.gt_eq(P.pair(P.g1_mul(g1, a), g2), P.gt_pow(base, a))
    assert P.gt_eq(P.pair(g1, P.g2_mul(g2, a)), P.gt_pow(base, a))


def test_gt_inverse():
    base = P.pair(P.g1_generator(), P.g2_generator())
    assert P.gt_eq(P.gt_mul(base, P.gt_inv(base)), P.gt_one())


def test_serialization_is_deterministic_and_distinguishing():
    g1 = P.g1_generator()
    assert P.g1_to_bytes(g1) == P.g1_to_bytes(g1)
    assert P.g1_to_bytes(g1) != P.g1_to_bytes(P.g1_mul(g1, 2))
    g2 = P.g2_generator()
    assert P.g2_to_bytes(g2) == P.g2_to_bytes(g2)
    assert P.g2_to_bytes(g2) != P.g2_to_bytes(P.g2_mul(g2, 2))


def test_hash_to_scalar_deterministic_in_range_and_prefix_safe():
    h1 = P.hash_to_scalar(b"hello", b"world")
    h2 = P.hash_to_scalar(b"hello", b"world")
    h3 = P.hash_to_scalar(b"helloworld", b"")
    assert h1 == h2
    assert 0 <= h1 < P.ORDER
    assert h1 != h3
