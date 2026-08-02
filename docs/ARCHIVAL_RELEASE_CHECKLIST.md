# Public archival release checklist

**Status: COMPLETE**

The SWAN-MPO public software and reproducibility infrastructure has completed its release, archival, and public-access verification gates.

## Public endpoints

- Source repository: https://github.com/saanviisenthilkumar/swan-mpo
- Public software release: `v1.3.2`
- Release commit: `e1705f0c92c3b850a22957585100e86da891644f`
- Zenodo archived software release: https://doi.org/10.5281/zenodo.21753539
- OSF reproducibility record: https://osf.io/35qf2/

## Completed release gates

1. The post-audit scientific implementation passed Mac validation, actual AutoDock Vina 1.2.7 integration, strict verification, and the clean-clone gate.
2. The public `v1.3.2` software release was created from the finalized release snapshot.
3. The release was archived on Zenodo with version-specific DOI `10.5281/zenodo.21753539`.
4. The manuscript-reproduction data bundle was deposited on OSF.
5. Logged-out/incognito access was verified for GitHub, Zenodo, and OSF.
6. The public reproduction workflow reproduces 177 panel-level rows and 531 target-level rows with zero failures.
7. Muricatacin reproduces at Colon rank 1, Prostate rank 2, and RCC rank 2.
8. Release and license audits pass with zero bundled blocked structural assets.
9. The frozen model and published calibration remain hash-locked.
10. File-level SHA-256 provenance is retained in the repository manifest.

## Frozen identifiers

Locked model SHA-256:

`97799e91f23803de3b9a477aea3bbcfb061f1b1d9abebdecfdadcd1b537f4454`

Published target-calibration SHA-256:

`e7584f10c0f970bb54ddf39cfdacbb6cb061bc6a3d2bd795e2d5f119efc7287c`

OSF manuscript-reproduction bundle SHA-256:

`2dd676b9347149a36f6ab302a21be04f28f225111a57a0ceee7676ed62233e0f`

## Public reproduction resources

The archived/public resources provide access to:

- source code and CLI;
- `manuscript_source_manifest.json`;
- canonical SwissADME input;
- exact unchanged ProTox input;
- the 10,620-row scoring-required docking extract;
- 177-row expected panel outputs;
- 531-row expected target-level outputs;
- the published target-calibration resource;
- installation and reproduction documentation.

The expanded-screen regression is reproduced with:

`swan-mpo reproduce-manuscript --output-dir manuscript_reproduction`

## Data-availability reference

The SWAN-MPO source code and frozen software release are publicly available through GitHub and Zenodo. Manuscript-reproduction inputs and supporting provenance materials are additionally available through OSF. File-specific licensing and third-party attribution are documented in `DATA_LICENSE.md` and `THIRD_PARTY_NOTICES.md`.
