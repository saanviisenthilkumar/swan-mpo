import math
import pytest
from swan_mpo import locked_model as m


def test_ld50_anchor_low():
    assert m.ld50_desirability(50) == 0.01


def test_ld50_anchor_high():
    assert m.ld50_desirability(5000) == 1.0


def test_ld50_invalid_is_missing():
    assert math.isnan(m.ld50_desirability(0))


def test_toxicity_class_endpoints():
    assert m.toxicity_class_desirability(1) == 0.01
    assert m.toxicity_class_desirability(6) == 1.0


def test_unknown_toxicity_endpoint_defaults_to_half():
    assert m.toxicity_endpoint_desirability('unknown') == 0.5


def test_pains_handling():
    zero = m.calculate_adme(mw=400, consensus_logp=3, tpsa=80, rotatable_bonds=4,
                            hba=4, hbd=1, pains_alerts=0, gi_absorption='High', synthetic_accessibility=3)
    present = m.calculate_adme(mw=400, consensus_logp=3, tpsa=80, rotatable_bonds=4,
                               hba=4, hbd=1, pains_alerts=1, gi_absorption='High', synthetic_accessibility=3)
    missing = m.calculate_adme(mw=400, consensus_logp=3, tpsa=80, rotatable_bonds=4,
                               hba=4, hbd=1, pains_alerts='', gi_absorption='High', synthetic_accessibility=3)
    assert zero['d_pains'] == 1.0
    assert present['d_pains'] == 0.25
    assert missing['d_pains'] == 0.50


def test_gi_handling():
    high = m.calculate_adme(mw=400, consensus_logp=3, tpsa=80, rotatable_bonds=4,
                            hba=4, hbd=1, pains_alerts=0, gi_absorption='High', synthetic_accessibility=3)
    low = m.calculate_adme(mw=400, consensus_logp=3, tpsa=80, rotatable_bonds=4,
                           hba=4, hbd=1, pains_alerts=0, gi_absorption='Low', synthetic_accessibility=3)
    unknown = m.calculate_adme(mw=400, consensus_logp=3, tpsa=80, rotatable_bonds=4,
                               hba=4, hbd=1, pains_alerts=0, gi_absorption='', synthetic_accessibility=3)
    assert high['d_gi'] == 1.0
    assert low['d_gi'] == 0.35
    assert unknown['d_gi'] == 0.50


def test_panel_aliases_reproduce_liability_equations():
    a = m.calculate_liability(panel='CRC', bbb='Inactive 0.8', complex_i='Active 0.9', neuro='Inactive 0.7')
    b = m.calculate_liability(panel='Colon', bbb='Inactive 0.8', complex_i='Active 0.9', neuro='Inactive 0.7')
    assert a['liability_score'] == b['liability_score']
    c = m.calculate_liability(panel='kidney', bbb='Inactive 0.8', complex_i='Active 0.9', neuro='Inactive 0.7')
    d = m.calculate_liability(panel='RCC', bbb='Inactive 0.8', complex_i='Active 0.9', neuro='Inactive 0.7')
    assert c['liability_score'] == d['liability_score']


def test_unsupported_panel_raises():
    with pytest.raises(ValueError):
        m.calculate_liability(panel='Melanoma', bbb='Inactive 0.8', complex_i='Inactive 0.8', neuro='Inactive 0.8')


def test_geometric_mean_all_missing_returns_nan():
    assert math.isnan(m.geometric_mean([None, float('nan'), '']))


def test_colon_liability_is_invariant_to_complex_i_by_design():
    a = m.calculate_liability(panel='Colon', bbb='Inactive 0.9', complex_i='Active 0.99', neuro='Inactive 0.9')
    b = m.calculate_liability(panel='Colon', bbb='Inactive 0.9', complex_i='Inactive 0.50', neuro='Inactive 0.9')
    assert a['liability_score'] == b['liability_score']
