import stat
import pytest
from swan_mpo.vina_redocking import require_vina_version


def make_fake(tmp_path, text):
    p=tmp_path/'vina_fake.py'
    p.write_text('#!/usr/bin/env python3\nimport sys\nprint(%r)\n' % text)
    p.chmod(p.stat().st_mode | stat.S_IEXEC)
    return p


def test_exact_vina_1_2_7_version_is_accepted(tmp_path):
    fake=make_fake(tmp_path,'AutoDock Vina v1.2.7')
    assert require_vina_version(str(fake)) == '1.2.7'


def test_other_vina_version_is_rejected(tmp_path):
    fake=make_fake(tmp_path,'AutoDock Vina v1.2.6')
    with pytest.raises(Exception, match='version mismatch'):
        require_vina_version(str(fake))
