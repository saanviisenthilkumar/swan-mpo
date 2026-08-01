from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable

import networkx as nx

from .errors import InputValidationError

# Common AutoDock/PDBQT atom types -> element symbols.
_PDBQT_ELEMENT = {
    "A": "C",
    "C": "C",
    "N": "N",
    "NA": "N",
    "NS": "N",
    "OA": "O",
    "O": "O",
    "OS": "O",
    "S": "S",
    "SA": "S",
    "P": "P",
    "F": "F",
    "CL": "Cl",
    "BR": "Br",
    "I": "I",
    "MG": "Mg",
    "MN": "Mn",
    "ZN": "Zn",
    "FE": "Fe",
    "CA": "Ca",
}

_ATOMIC_NUMBER = {
    "H": 1,
    "C": 6,
    "N": 7,
    "O": 8,
    "F": 9,
    "P": 15,
    "S": 16,
    "Cl": 17,
    "Ca": 20,
    "Mn": 25,
    "Fe": 26,
    "Zn": 30,
    "Br": 35,
    "I": 53,
    "Mg": 12,
}

# Covalent radii (A), only for bond perception of the *native ligand* graph.
# Values are intentionally conservative; RMSD is fixed-frame and the graph is
# used only to identify automorphisms/symmetry-equivalent atom mappings.
_COVALENT_RADIUS = {
    "C": 0.76,
    "N": 0.71,
    "O": 0.66,
    "F": 0.57,
    "P": 1.07,
    "S": 1.05,
    "Cl": 1.02,
    "Br": 1.20,
    "I": 1.39,
    "Mg": 1.41,
    "Ca": 1.76,
    "Mn": 1.39,
    "Fe": 1.32,
    "Zn": 1.22,
}


@dataclass(frozen=True)
class HeavyAtom:
    name: str
    atom_type: str
    element: str
    atomic_number: int
    xyz: tuple[float, float, float]


def pdbqt_element(atom_type: str, atom_name: str = "") -> str:
    token = str(atom_type).strip()
    upper = token.upper()
    if upper in {"HD", "HS", "H"} or upper.startswith("H"):
        return "H"
    if upper in _PDBQT_ELEMENT:
        return _PDBQT_ELEMENT[upper]
    # Fallback to atom-name inference. Prefer two-character halogens.
    name = "".join(ch for ch in str(atom_name) if ch.isalpha())
    if len(name) >= 2 and name[:2].title() in _ATOMIC_NUMBER:
        return name[:2].title()
    if name and name[0].upper() in _ATOMIC_NUMBER:
        return name[0].upper()
    raise InputValidationError(
        f"Could not infer element from PDBQT atom type {atom_type!r} / atom name {atom_name!r}."
    )


def parse_pdbqt_atom(line: str) -> HeavyAtom | None:
    if not line.startswith(("ATOM  ", "HETATM")):
        return None
    try:
        name = line[12:16].strip()
        x = float(line[30:38])
        y = float(line[38:46])
        z = float(line[46:54])
    except Exception:
        parts = line.split()
        if len(parts) < 8:
            return None
        name = parts[2]
        try:
            x, y, z = map(float, parts[5:8])
        except Exception:
            return None
    parts = line.split()
    atom_type = parts[-1] if parts else ""
    element = pdbqt_element(atom_type, name)
    if element == "H":
        return None
    atomic_number = _ATOMIC_NUMBER.get(element)
    if atomic_number is None:
        raise InputValidationError(f"Unsupported heavy-atom element {element!r} in PDBQT.")
    return HeavyAtom(name, atom_type, element, atomic_number, (x, y, z))


def ordered_fixed_frame_heavy_atom_rmsd(native_atoms: list[HeavyAtom], pose_atoms: list[HeavyAtom]) -> float:
    if len(native_atoms) != len(pose_atoms):
        raise InputValidationError(
            f"Native/docked ligand heavy-atom counts differ ({len(native_atoms)} vs {len(pose_atoms)})."
        )
    for index, (native, pose) in enumerate(zip(native_atoms, pose_atoms), start=1):
        if native.atomic_number != pose.atomic_number:
            raise InputValidationError(
                f"Native/docked atom element mismatch at heavy atom {index}: {native.element} vs {pose.element}. "
                "Ordered RMSD is unsafe when atom ordering changes."
            )
    squared = 0.0
    for native, pose in zip(native_atoms, pose_atoms):
        squared += sum((a - b) ** 2 for a, b in zip(native.xyz, pose.xyz))
    return math.sqrt(squared / len(native_atoms))


def _distance(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def infer_native_graph(native_atoms: list[HeavyAtom], tolerance_A: float = 0.45) -> nx.Graph:
    graph = nx.Graph()
    for index, atom in enumerate(native_atoms):
        graph.add_node(index, atomic_number=atom.atomic_number, element=atom.element)
    for i, atom_i in enumerate(native_atoms):
        radius_i = _COVALENT_RADIUS.get(atom_i.element)
        if radius_i is None:
            raise InputValidationError(f"No covalent radius available for {atom_i.element!r}.")
        for j in range(i + 1, len(native_atoms)):
            atom_j = native_atoms[j]
            radius_j = _COVALENT_RADIUS.get(atom_j.element)
            if radius_j is None:
                raise InputValidationError(f"No covalent radius available for {atom_j.element!r}.")
            cutoff = radius_i + radius_j + tolerance_A
            if _distance(atom_i.xyz, atom_j.xyz) <= cutoff:
                graph.add_edge(i, j)
    if graph.number_of_edges() == 0 and len(native_atoms) > 1:
        raise InputValidationError(
            "Native-ligand connectivity could not be perceived from PDBQT coordinates. "
            "Use --rmsd-backend ordered only after confirming PDBQT atom order is preserved, "
            "or provide a better prepared native ligand."
        )
    return graph


def symmetry_corrected_fixed_frame_heavy_atom_rmsd(
    native_atoms: list[HeavyAtom],
    pose_atoms: list[HeavyAtom],
    *,
    max_automorphisms: int = 10000,
) -> tuple[float, int]:
    """Fixed-receptor-frame RMSD minimized over graph isomorphisms.

    Unlike superposition RMSD, coordinates are *not* aligned. This preserves the
    crystallographic/receptor frame used for redocking validation while allowing
    symmetry-equivalent heavy atoms to exchange labels.
    """
    if len(native_atoms) != len(pose_atoms):
        raise InputValidationError(
            f"Native/docked ligand heavy-atom counts differ ({len(native_atoms)} vs {len(pose_atoms)})."
        )
    if sorted(atom.atomic_number for atom in native_atoms) != sorted(atom.atomic_number for atom in pose_atoms):
        raise InputValidationError("Native/docked ligand heavy-atom element multisets differ.")

    native_graph = infer_native_graph(native_atoms)
    pose_graph = infer_native_graph(pose_atoms)
    matcher = nx.algorithms.isomorphism.GraphMatcher(
        native_graph,
        pose_graph,
        node_match=lambda a, b: a.get("atomic_number") == b.get("atomic_number"),
    )
    best = float("inf")
    count = 0
    for mapping in matcher.isomorphisms_iter():
        count += 1
        if count > max_automorphisms:
            raise InputValidationError(
                f"Ligand has more than {max_automorphisms} graph isomorphisms. "
                "Refusing an unbounded symmetry search; use an independently validated RMSD tool."
            )
        squared = 0.0
        # GraphMatcher(native_graph, pose_graph) maps native indices to pose
        # indices, so arbitrary atom ordering and symmetry-equivalent labels are
        # both handled without geometric superposition.
        for native_index, pose_index in mapping.items():
            native = native_atoms[native_index]
            pose = pose_atoms[pose_index]
            if native.atomic_number != pose.atomic_number:
                squared = float("inf")
                break
            squared += sum((a - b) ** 2 for a, b in zip(native.xyz, pose.xyz))
        rmsd = math.sqrt(squared / len(native_atoms))
        if rmsd < best:
            best = rmsd
    if not math.isfinite(best):
        raise InputValidationError(
            "No element/connectivity-preserving graph isomorphism was found between the native and docked ligand. "
            "Inspect ligand preparation and atom typing before using the RMSD for target calibration."
        )
    return best, count


def calculate_redocking_rmsd(
    native_atoms: list[HeavyAtom],
    pose_atoms: list[HeavyAtom],
    *,
    backend: str = "symmetry",
) -> tuple[float, str, int]:
    backend = str(backend).strip().lower()
    if backend == "symmetry":
        value, automorphisms = symmetry_corrected_fixed_frame_heavy_atom_rmsd(native_atoms, pose_atoms)
        return value, "symmetry_corrected_fixed_frame_graph_automorphism", automorphisms
    if backend == "ordered":
        value = ordered_fixed_frame_heavy_atom_rmsd(native_atoms, pose_atoms)
        return value, "ordered_fixed_frame_heavy_atom", 1
    raise InputValidationError("RMSD backend must be 'symmetry' or 'ordered'.")
