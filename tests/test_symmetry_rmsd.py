from swan_mpo.rmsd import HeavyAtom, symmetry_corrected_fixed_frame_heavy_atom_rmsd, ordered_fixed_frame_heavy_atom_rmsd


def atom(name, element, z, x, y=0.0, zz=0.0):
    return HeavyAtom(name, element, element, z, (x, y, zz))


def test_symmetry_corrects_equivalent_atom_swap_without_superposition():
    # Linear O-C-O: the terminal oxygens are symmetry-equivalent. The docked atom
    # list is deliberately reordered. Fixed-frame symmetry correction should find
    # the zero-displacement correspondence while ordered RMSD is nonzero.
    native = [atom('O1','O',8,-1.2), atom('C','C',6,0.0), atom('O2','O',8,1.2)]
    pose = [atom('O2','O',8,1.2), atom('C','C',6,0.0), atom('O1','O',8,-1.2)]
    value, mappings = symmetry_corrected_fixed_frame_heavy_atom_rmsd(native, pose)
    assert value < 1e-12
    assert mappings >= 2
    assert ordered_fixed_frame_heavy_atom_rmsd(native, pose) > 1.0


def test_fixed_frame_rmsd_does_not_align_away_translation():
    native = [atom('C1','C',6,0.0), atom('O1','O',8,1.2)]
    pose = [atom('C1','C',6,2.0), atom('O1','O',8,3.2)]
    value, _ = symmetry_corrected_fixed_frame_heavy_atom_rmsd(native, pose)
    assert abs(value - 2.0) < 1e-12
