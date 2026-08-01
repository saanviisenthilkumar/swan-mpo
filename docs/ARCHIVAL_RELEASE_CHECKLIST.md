# Public archival release checklist

This checklist closes the final *publication-state* part of the JoC reproducibility requirement after the code/data payload itself has passed RC2 verification.

1. Push and tag the post-audit release candidate after the Mac + real-Vina + clean-clone gates pass.
2. Create the public code release and archival record (GitHub release + Zenodo and/or OSF as selected).
3. Include the repository's manuscript-reproduction resources in the archived release; do not replace them with newly generated files unless the SHA-256 manifest is intentionally versioned and revalidated.
4. Confirm the following are accessible without login using an incognito/not-signed-in browser:
   - source code;
   - `manuscript_source_manifest.json`;
   - canonical SwissADME input;
   - exact unchanged ProTox input;
   - 10,620-row scoring-required docking extract;
   - 177-row and 531-row expected outputs;
   - published target-calibration resource;
   - installation/reproduction documentation.
5. Run `swan-mpo reproduce-manuscript --output-dir manuscript_reproduction` from a clean clone of the public tag.
6. Confirm `swan-mpo verify --manuscript` passes from the same clone.
7. Record the final public Git commit/tag and archival DOI in the manuscript Availability of Data and Materials section.
8. Re-open every manuscript link from a logged-out browser before submission.

## Availability-of-data wording template

Replace bracketed placeholders only after the public endpoints exist:

> **Availability of data and materials.** The SWAN-MPO source code, frozen model, target-calibration resource, exact expanded-screen ADME and toxicity inputs, scoring-required 10,620-row docking extract, canonical expected outputs, tests, and one-command manuscript-reproduction workflow are available in the public repository at [GITHUB URL] and archived at [DOI/ARCHIVE URL]. The tagged release permits reproduction of the 59-compound expanded screen using `swan-mpo reproduce-manuscript`. File-level SHA-256 provenance is provided in the release manifest. No receptor/native-ligand structural files requiring separate upstream redistribution are bundled; reference-redocking configuration and provenance are documented separately.
