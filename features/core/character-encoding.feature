Feature: Encode file names to work effectively across a heterogeneous set of
         tools

	Alma receives archival materials from multiple heterogeneous sources.
	Archivematica should be able to receive multiple different character
	encodings from a collection and ensure that the files can be piped into
	its many embedded tools so that their output can be parsed on the way to
	generating an AIP that describes the accession.

	Scenario: Original path names persist into the archival package’s
		METS/PREMIS
		Given a collection with <Encoding> in file paths
		When the <Archival Package> is created
		Then the original path with the original <Encoding> encoding can always
		be recreated from the content of the METS/PREMIS

	Examples:
		| Encoding | Archival Packages |
		| ShiftJS  |        AIP        |
		| UTF-8    |        DIP        |
		| UTF-16   |        SIP        |
		| ASCII    |                   |
		| EBCIDIC  |                   |
