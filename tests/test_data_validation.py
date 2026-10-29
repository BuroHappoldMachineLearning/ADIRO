"""The data-validation shapes (#168): each rule is shown to accept a conforming graph and to reject a violating one."""
import sys
from pathlib import Path

import pytest

pytest.importorskip("rdflib")
pytest.importorskip("pyshacl")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from rdflib import Graph, URIRef  # noqa: E402
from rdflib.namespace import RDF  # noqa: E402

import validate_data as vd  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PREFIXES = """@prefix : <https://ex.org/d#> .
@prefix metadata: <https://w3id.org/adiro/adiro_drawing_metadata#> .
@prefix csymbol: <https://w3id.org/adiro/adiro_common_symbols#> .
"""


def check(body):
    return vd.validate(Graph().parse(data=PREFIXES + body, format="turtle"), ROOT)


def messages(body):
    return [r["message"] for r in check(body)]


# --- the inline reference: one drawing identifier, at least one layout identifier -----------------------------------
INLINE_OK = """:ref a metadata:InlineLayoutSheetReference ; metadata:contains :sheet , :l1 , :l3 .
:sheet a metadata:DrawingIdentifierMention .
:l1 a metadata:LayoutIdentifierMention . :l3 a metadata:LayoutIdentifierMention .
"""


def test_a_complete_inline_reference_conforms():
    assert check(INLINE_OK) == []


def test_an_inline_reference_with_two_drawing_identifiers_is_reported():
    two = INLINE_OK + ":other a metadata:DrawingIdentifierMention . :ref metadata:contains :other .\n"
    assert messages(two) == ["An inline layout and sheet reference contains exactly one drawing identifier mention."]


def test_an_inline_reference_with_no_drawing_identifier_is_reported():
    none = """:ref a metadata:InlineLayoutSheetReference ; metadata:contains :l1 .
:l1 a metadata:LayoutIdentifierMention .
"""
    assert messages(none) == ["An inline layout and sheet reference contains exactly one drawing identifier mention."]


def test_an_inline_reference_with_no_layout_identifier_is_reported():
    none = """:ref a metadata:InlineLayoutSheetReference ; metadata:contains :sheet .
:sheet a metadata:DrawingIdentifierMention .
"""
    assert messages(none) == ["An inline layout and sheet reference contains at least one layout identifier mention."]


def test_a_standalone_reference_counts_as_a_drawing_identifier_mention():
    # StandaloneSheetReference is a subclass of DrawingIdentifierMention: the ontology is read as background.
    nested = """:ref a metadata:InlineLayoutSheetReference ; metadata:contains :sheet , :l1 .
:sheet a metadata:StandaloneSheetReference . :l1 a metadata:LayoutIdentifierMention .
"""
    assert check(nested) == []


# --- the reference symbol: at most one drawing identifier ------------------------------------------------------------
def test_a_reference_symbol_with_at_most_one_drawing_identifier_conforms():
    assert check(":s a csymbol:ReferenceSymbol .\n") == []
    assert check(":s a csymbol:ReferenceSymbol ; metadata:contains :m . :m a metadata:DrawingIdentifierMention .\n") == []


def test_a_reference_symbol_with_two_drawing_identifiers_is_reported():
    two = ":s a csymbol:ReferenceSymbol ; metadata:contains :a , :b . :a a metadata:DrawingIdentifierMention . :b a metadata:DrawingIdentifierMention .\n"
    assert messages(two) == ["A reference symbol contains at most one drawing identifier mention."]


# --- a mention has at most one accepted target -----------------------------------------------------------------------
def test_a_mention_with_one_target_conforms_and_with_two_is_reported():
    one = ":m a metadata:DrawingIdentifierMention ; metadata:denotesDrawingSheet :s1 .\n"
    two = one + ":m metadata:denotesDrawingSheet :s2 .\n"
    assert check(one) == []
    assert messages(two) == ["A drawing identifier mention has at most one accepted denotesDrawingSheet target."]


def test_the_rule_reaches_a_standalone_reference_through_its_superclass():
    two = ":m a metadata:StandaloneSheetReference ; metadata:denotesDrawingSheet :s1 , :s2 .\n"
    assert messages(two) == ["A drawing identifier mention has at most one accepted denotesDrawingSheet target."]


def test_a_violation_is_reported_with_its_severity_and_focus():
    result = check(":m a metadata:DrawingIdentifierMention ; metadata:denotesDrawingSheet :s1 , :s2 .\n")[0]
    assert result["severity"] == "Violation" and result["focus"] == "https://ex.org/d#m"
    assert result["path"].endswith("denotesDrawingSheet")


def test_the_command_line_exits_one_on_a_violation_and_zero_otherwise(tmp_path):
    bad, good = tmp_path / "bad.ttl", tmp_path / "good.ttl"
    bad.write_text(PREFIXES + ":m a metadata:DrawingIdentifierMention ; metadata:denotesDrawingSheet :s1 , :s2 .\n", encoding="utf-8")
    good.write_text(PREFIXES + INLINE_OK, encoding="utf-8")
    assert vd.main([str(bad)]) == 1
    assert vd.main([str(good)]) == 0
    assert vd.main([]) == 2


# --- the shape files themselves --------------------------------------------------------------------------------------
def test_every_shape_has_a_message_and_a_severity():
    shapes = vd.load_shapes(ROOT, release=True)
    SH = vd.SH
    for shape in shapes.subjects(RDF.type, SH.NodeShape):
        assert shapes.value(shape, SH.severity) is not None, f"{shape} has no sh:severity"
        for constraint in shapes.objects(shape, SH.sparql):
            assert shapes.value(constraint, SH.message) is not None, f"a SPARQL constraint of {shape} has no sh:message"
        for prop in shapes.objects(shape, SH.property):
            assert shapes.value(prop, SH.message) is not None, f"a property shape of {shape} has no sh:message"
            # SHACL does not pass a node shape's severity down to its property shapes: without its own, the default
            # (Violation) applies, whatever the node shape says.
            assert shapes.value(prop, SH.severity) == shapes.value(shape, SH.severity), f"a property shape of {shape} has a different or no sh:severity"


def test_every_adiro_term_a_shape_names_exists_in_the_ontology():
    # A shape that names a term the ontology no longer has would silently match nothing.
    ontology = vd.load_ontology(ROOT)
    declared = set(ontology.subjects())
    shapes = vd.load_shapes(ROOT, release=True)
    named = {
        o for s, p, o in shapes
        if isinstance(o, URIRef) and str(o).startswith("https://w3id.org/adiro/adiro_")
    }
    named |= {p for _, p, _ in shapes if str(p).startswith("https://w3id.org/adiro/adiro_")}
    assert named, "the shapes name no ADIRO term"
    assert named - declared == set(), f"terms the ontology does not declare: {sorted(named - declared)}"


def test_the_shape_files_follow_the_naming_convention():
    files = vd.shape_files(ROOT)
    assert files, "no shape files"
    assert all(p.name.endswith(".shacl.ttl") for p in files)
    for folder in (vd.SHAPES_DIR, vd.RELEASE_DIR):
        stray = [p.name for p in (ROOT / folder).iterdir() if p.suffix == ".ttl" and not p.name.endswith(".shacl.ttl")]
        assert stray == [], f"a .ttl in {folder}/ that is not *.shacl.ttl is never run: {stray}"
    release = vd.shape_files(ROOT, release=True)
    assert set(files) < set(release), "the release adds its own shapes to the others"


# --- UC-01: a drawing has an author (#179) -----------------------------------------------------------------------------
def test_a_drawing_with_an_author_conforms():
    assert check(":d a metadata:DrawingSheet ; metadata:isAuthoredBy :jsmith .\n") == []


def test_a_drawing_with_no_author_is_a_warning_and_never_fails_a_run(tmp_path):
    results = check(":d a metadata:DrawingSheet .\n")
    assert [(r["severity"], r["message"]) for r in results] == [("Warning", "A drawing has at least one recorded author.")]
    data = tmp_path / "d.ttl"
    data.write_text(PREFIXES + ":d a metadata:DrawingSheet .\n", encoding="utf-8")
    assert vd.main([str(data)]) == 0  # a warning is reported; only a violation fails the run


def test_a_drawing_with_no_author_of_its_own_is_read_as_authored_by_its_revisions_authors():
    only_revision = ":d a metadata:DrawingSheet ; metadata:hasRevision :r . :r a metadata:DrawingRevision ; metadata:isAuthoredBy :jsmith .\n"
    assert check(only_revision) == []
    # only the author has the fallback, and a revision that is not linked to the drawing counts for nothing
    checked_only = ":d a metadata:DrawingSheet ; metadata:hasRevision :r . :r a metadata:DrawingRevision ; metadata:isCheckedBy :achen .\n"
    assert [r["severity"] for r in check(checked_only)] == ["Warning"]
    unlinked = ":d a metadata:DrawingSheet . :r a metadata:DrawingRevision ; metadata:isAuthoredBy :jsmith .\n"
    assert [r["severity"] for r in check(unlinked)] == ["Warning"]


def test_the_checker_and_the_approver_are_optional():
    assert check(":d a metadata:DrawingSheet ; metadata:isAuthoredBy :jsmith .\n") == []  # no checker, no approver: no result


# --- field assertions: a value or an outcome, an agent when accepted, the same thing when superseding (#187) ----------
APROV = "@prefix aprov: <https://w3id.org/adiro/adiro_provenance#> .\n"


def check_assertions(body):
    return vd.validate(Graph().parse(data=PREFIXES + APROV + body, format="turtle"), ROOT)


def test_an_assertion_with_a_value_or_with_an_outcome_conforms():
    assert check_assertions(':a a aprov:FieldAssertion ; aprov:hasLiteralValue "J. Smith" .\n') == []
    assert check_assertions(":a a aprov:FieldAssertion ; aprov:hasOutcome aprov:NotPrinted .\n") == []
    assert check_assertions(":a a aprov:FieldAssertion .\n") == []  # still being filled in


def test_an_assertion_with_both_a_value_and_an_outcome_is_reported():
    both = ':a a aprov:FieldAssertion ; aprov:hasLiteralValue "J. Smith" ; aprov:hasOutcome aprov:Empty .\n'
    assert [r["message"] for r in check_assertions(both)] == ["An assertion has a value or an outcome, never both."]
    entity = ":a a aprov:FieldAssertion ; aprov:hasValueEntity :p ; aprov:hasOutcome aprov:Illegible .\n"
    assert len(check_assertions(entity)) == 1


def test_an_accepted_assertion_needs_an_agent_and_a_pending_one_does_not():
    assert [r["message"] for r in check_assertions(":a a aprov:FieldAssertion ; aprov:hasAcceptance aprov:Accepted .\n")] == [
        "An accepted assertion has an acceptedBy."]
    assert check_assertions(":a a aprov:FieldAssertion ; aprov:hasAcceptance aprov:Accepted ; aprov:acceptedBy :reviewer .\n") == []
    assert check_assertions(":a a aprov:FieldAssertion ; aprov:hasAcceptance aprov:Pending .\n") == []
    assert check_assertions(":a a aprov:FieldAssertion ; aprov:hasAcceptance aprov:Rejected .\n") == []


def test_a_superseding_assertion_is_about_the_same_subject_and_kind():
    same = """:old a aprov:FieldAssertion ; aprov:assertedAbout :d ; aprov:assertsFieldKind :k .
:new a aprov:FieldAssertion ; aprov:assertedAbout :d ; aprov:assertsFieldKind :k ; aprov:supersedes :old .
"""
    assert check_assertions(same) == []
    other_kind = same.replace(":new a aprov:FieldAssertion ; aprov:assertedAbout :d ; aprov:assertsFieldKind :k",
                              ":new a aprov:FieldAssertion ; aprov:assertedAbout :d ; aprov:assertsFieldKind :other")
    assert [r["message"] for r in check_assertions(other_kind)] == ["An assertion supersedes another about the same subject and the same field kind."]
    other_subject = same.replace(":new a aprov:FieldAssertion ; aprov:assertedAbout :d", ":new a aprov:FieldAssertion ; aprov:assertedAbout :e")
    assert len(check_assertions(other_subject)) == 1


def test_an_assertion_does_not_supersede_itself_through_a_chain():
    chain = """:a a aprov:FieldAssertion ; aprov:assertedAbout :d ; aprov:assertsFieldKind :k .
:b a aprov:FieldAssertion ; aprov:assertedAbout :d ; aprov:assertsFieldKind :k ; aprov:supersedes :a .
:c a aprov:FieldAssertion ; aprov:assertedAbout :d ; aprov:assertsFieldKind :k ; aprov:supersedes :b .
"""
    assert check_assertions(chain) == []
    cycle = chain + ":a aprov:supersedes :c .\n"
    message = "An assertion does not supersede itself, directly or through other assertions."
    assert sorted((r["focus"].rsplit("#", 1)[-1], r["message"]) for r in check_assertions(cycle)) == [
        ("a", message), ("b", message), ("c", message)]
    assert [r["message"] for r in check_assertions(chain + ":a aprov:supersedes :a .\n")] == [message]


# --- one acceptance status and at most one outcome, each from its published list (#220) ------------------------------
STATUS = "An acceptance status is Pending, Accepted or Rejected."
OUTCOME = "An outcome is Empty, Illegible, NotPrinted, NotFound or Failed."


def test_an_assertion_accepted_and_rejected_is_reported_even_with_an_agent():
    both = (':a a aprov:FieldAssertion ; aprov:hasLiteralValue "Ground Floor Plan" ;'
            " aprov:hasAcceptance aprov:Accepted , aprov:Rejected ; aprov:acceptedBy :reviewer .\n")
    assert messages_of(both) == ["An assertion has at most one acceptance status."]


def test_an_assertion_with_two_outcomes_is_reported():
    assert messages_of(":a a aprov:FieldAssertion ; aprov:hasOutcome aprov:NotPrinted , aprov:Illegible .\n") == [
        "An assertion has at most one outcome."]


def test_a_status_or_an_outcome_outside_its_list_is_reported():
    assert messages_of(":a a aprov:FieldAssertion ; aprov:hasAcceptance :Acceptted .\n") == [STATUS]
    assert messages_of(':a a aprov:FieldAssertion ; aprov:hasAcceptance "Accepted" .\n') == [STATUS]
    assert messages_of(":a a aprov:FieldAssertion ; aprov:hasAcceptance aprov:NotPrinted .\n") == [STATUS]  # an outcome
    assert messages_of(":a a aprov:FieldAssertion ; aprov:hasOutcome :NotPrnted .\n") == [OUTCOME]
    assert messages_of(':a a aprov:FieldAssertion ; aprov:hasOutcome "NotPrinted" .\n') == [OUTCOME]
    assert messages_of(":a a aprov:FieldAssertion ; aprov:hasOutcome aprov:Rejected .\n") == [OUTCOME]  # a status


def test_each_allowed_status_and_outcome_conforms():
    for status in ("Pending", "Rejected"):
        assert check_assertions(f':a a aprov:FieldAssertion ; aprov:hasLiteralValue "X" ; aprov:hasAcceptance aprov:{status} .\n') == []
    accepted = ':a a aprov:FieldAssertion ; aprov:hasLiteralValue "X" ; aprov:hasAcceptance aprov:Accepted'
    assert check_assertions(accepted + " ; aprov:acceptedBy :reviewer .\n") == []
    assert messages_of(accepted + " .\n") == ["An accepted assertion has an acceptedBy."]
    for outcome in ("Empty", "Illegible", "NotPrinted", "NotFound", "Failed"):
        assert check_assertions(f":a a aprov:FieldAssertion ; aprov:hasOutcome aprov:{outcome} ; aprov:hasAcceptance aprov:Pending .\n") == []


def test_different_assertions_about_one_field_may_disagree():
    # disagreement or history is kept as separate assertions, each with its own current status
    two = """:a1 a aprov:FieldAssertion ; aprov:assertedAbout :d ; aprov:assertsFieldKind :k ; aprov:hasLiteralValue "Plan" ;
    aprov:hasAcceptance aprov:Accepted ; aprov:acceptedBy :reviewer .
:a2 a aprov:FieldAssertion ; aprov:assertedAbout :d ; aprov:assertsFieldKind :k ; aprov:hasOutcome aprov:Illegible ;
    aprov:hasAcceptance aprov:Rejected .
:a3 a aprov:FieldAssertion ; aprov:assertedAbout :d ; aprov:assertsFieldKind :k ; aprov:hasOutcome aprov:NotPrinted .
"""
    assert check_assertions(two) == []


def test_the_cli_reports_the_cases_of_the_issue(tmp_path, capsys):
    data = tmp_path / "assertion-cases.ttl"
    data.write_text(PREFIXES + APROV + """
:bothStatuses a aprov:FieldAssertion ; aprov:assertedAbout :drawing ; aprov:hasLiteralValue "Ground Floor Plan" ;
    aprov:hasAcceptance aprov:Accepted , aprov:Rejected ; aprov:acceptedBy :reviewer .
:bothOutcomes a aprov:FieldAssertion ; aprov:hasOutcome aprov:NotPrinted , aprov:Illegible .
:unknownStatus a aprov:FieldAssertion ; aprov:hasAcceptance :Acceptted .
:unknownOutcome a aprov:FieldAssertion ; aprov:hasOutcome :NotPrnted .
""", encoding="utf-8")
    assert vd.main([str(data)]) == 1
    out = capsys.readouterr().out
    for name in ("bothStatuses", "bothOutcomes", "unknownStatus", "unknownOutcome"):
        assert f"[Violation] https://ex.org/d#{name}:" in out
    assert "4 result(s), 4 violation(s)" in out


def messages_of(body):
    return [r["message"] for r in check_assertions(body)]


# --- a file records where it came from, itself or through the file it was derived from (#229) ---------------------------
PROV = "@prefix prov: <http://www.w3.org/ns/prov#> .\n@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .\n"
NO_SOURCE = "A file records where it was obtained from (sourceLocation), or was derived from a file that does."


def check_files(body, public_hosts=None):
    return vd.validate(Graph().parse(data=PREFIXES + APROV + PROV + body, format="turtle"), ROOT, public_hosts)


def test_a_file_with_a_source_conforms():
    assert check_files(':f a aprov:DrawingFile ; aprov:sourceLocation "https://tile.loc.gov/a.tif"^^xsd:anyURI .\n') == []


def test_a_file_with_no_source_is_a_warning():
    results = check_files(":f a aprov:DrawingFile .\n")
    assert [(r["severity"], r["message"]) for r in results] == [("Warning", NO_SOURCE)]


def test_a_derived_file_finds_its_source_through_the_files_it_was_made_from():
    chain = """:png a aprov:DrawingFile ; prov:wasDerivedFrom :pdf .
:pdf a aprov:DrawingFile ; prov:wasDerivedFrom :original .
:original a aprov:DrawingFile ; aprov:sourceLocation "https://example.org/set.pdf"^^xsd:anyURI .
"""
    assert check_files(chain) == []
    no_origin = chain.replace(' ; aprov:sourceLocation "https://example.org/set.pdf"^^xsd:anyURI', "")
    assert sorted(r["focus"].rsplit("#", 1)[-1] for r in check_files(no_origin)) == ["original", "pdf", "png"]


# --- a public release names only addresses on a public host (#229) -------------------------------------------------------
NOT_PUBLIC = "is not on the allowlist."
HOSTS = ["loc.gov", "nomic-public-data.com"]


def released(body):
    return [r for r in check_files(body, HOSTS) if r["severity"] == "Violation"]


def test_addresses_on_a_public_host_or_its_subdomains_conform_in_a_release():
    public = """:f a aprov:DrawingFile ; aprov:sourceLocation "https://tile.loc.gov/storage-services/a.tif"^^xsd:anyURI ;
    aprov:sourcePage "https://www.loc.gov/item/x/"^^xsd:anyURI ;
    aprov:storageLocation "https://NOMIC-PUBLIC-DATA.com/set.pdf"^^xsd:anyURI .
"""
    assert released(public) == []


def test_an_address_off_the_allowlist_is_a_violation_in_a_release():
    internal = """:f a aprov:DrawingFile ; aprov:sourceLocation "https://tile.loc.gov/a.tif"^^xsd:anyURI ;
    aprov:storageLocation "https://intranet.example.com/sites/data/a.tif"^^xsd:anyURI .
"""
    results = released(internal)
    assert [(r["path"].rsplit("#", 1)[-1], r["message"].endswith(NOT_PUBLIC)) for r in results] == [("storageLocation", True)]


def test_a_look_alike_host_a_user_part_or_a_file_path_is_not_public():
    for address in ("https://evil-loc.gov/a.tif", "https://loc.gov.example.com/a.tif", "https://loc.gov@intranet.example.com/a.tif",
                    "file:///C:/data/a.tif", "C:/data/a.tif", "/mnt/share/loc.gov"):
        body = f':f a aprov:DrawingFile ; aprov:sourceLocation "{address}"^^xsd:anyURI .\n'
        assert len(released(body)) == 1, address


def test_a_backslash_a_space_or_a_line_break_never_passes_as_a_public_host():
    # A URL parser reads a backslash as a slash, so the real host of the first two is intranet.example.com
    for address in (r"https://intranet.example.com\\.loc.gov/a.tif", r"https://intranet\\@loc.gov/a.tif",
                    r"https://intranet.example.com/a\n.loc.gov", "https://intranet.example.com .loc.gov/a.tif",
                    r"https://loc.gov/a.tif\n"):
        body = f':f a aprov:DrawingFile ; aprov:sourceLocation "{address}"^^xsd:anyURI .\n'
        assert len(released(body)) == 1, address
    ok = ':f a aprov:DrawingFile ; aprov:sourceLocation "https://user@tile.loc.gov:443/a%20b.tif?x=1#p"^^xsd:anyURI .\n'
    assert released(ok) == []


def test_the_data_cannot_extend_the_allowlist():
    smuggled = """@prefix dvr: <https://w3id.org/adiro/data-validation/release#> .
[] a dvr:PublicHost ; dvr:host "example.com" .
:f a aprov:DrawingFile ; aprov:sourceLocation "https://intranet.example.com/a.tif"^^xsd:anyURI .
"""
    assert len(released(smuggled)) == 1


def test_an_acceptance_policy_off_the_allowlist_is_a_violation_in_a_release():
    policy = ':a a aprov:FieldAssertion ; aprov:acceptedUnder "https://intranet.example.com/policies/v3"^^xsd:anyURI .\n'
    results = released(policy)
    assert [(r["focus"].rsplit("#", 1)[-1], r["path"].rsplit("#", 1)[-1]) for r in results] == [("a", "acceptedUnder")]
    assert released(policy.replace("intranet.example.com", "tile.loc.gov")) == []


def test_the_release_rule_runs_only_for_a_release():
    internal = ':f a aprov:DrawingFile ; aprov:sourceLocation "https://intranet.example.com/a.tif"^^xsd:anyURI .\n'
    assert check_files(internal) == []  # the organisation's own data may name its own storage
    assert len(released(internal)) == 1


def test_the_cli_reads_the_allowlist_file(tmp_path, capsys):
    hosts = tmp_path / "hosts.txt"
    hosts.write_text("# public hosts\nloc.gov  # the Library of Congress\n\n", encoding="utf-8")
    assert vd.read_public_hosts(hosts) == ["loc.gov"]
    data = tmp_path / "files.ttl"
    data.write_text(PREFIXES + APROV + PROV + """:ok a aprov:DrawingFile ; aprov:sourceLocation "https://tile.loc.gov/a.tif"^^xsd:anyURI .
:leak a aprov:DrawingFile ; aprov:sourceLocation "https://intranet.example.com/a.tif"^^xsd:anyURI .
""", encoding="utf-8")
    assert vd.main([str(data)]) == 0
    assert vd.main(["--public-hosts", str(hosts), str(data)]) == 1
    out = capsys.readouterr().out
    assert "[Violation] https://ex.org/d#leak:" in out and "d#ok:" not in out
    assert "1 result(s), 1 violation(s)" in out
    assert vd.main(["--public-hosts"]) == 2


# --- a configuration of a step: exactly one content, as a string (#237) ---------------------------------------------------
def test_a_configuration_with_one_content_conforms():
    assert check_assertions(':c a aprov:Configuration ; aprov:configurationContent "Read the title block." .\n') == []


@pytest.mark.parametrize("body", [
    ":c a aprov:Configuration .\n",
    ':c a aprov:Configuration ; aprov:configurationContent "Read the title block." , "Read every field." .\n',
    ":c a aprov:Configuration ; aprov:configurationContent 300 .\n",
])
def test_a_configuration_with_no_content_two_contents_or_a_number_is_reported(body):
    assert [r["message"] for r in check_assertions(body)] == [
        "A configuration has exactly one configurationContent, as a string."]


# --- a text reading: one thing read, its text or one outcome (#238) -----------------------------------------------------
TEXT_OR_OUTCOME = "A reading has a text or an outcome, never both and never neither."


@pytest.mark.parametrize("body", [
    ':r a aprov:TextReading ; aprov:isReadingOf :titleblock ; aprov:readText "GROUND FLOOR PLAN" .\n',
    ':r a aprov:TextReading ; aprov:isReadingOf :page ; aprov:readText "Erdgeschoss"@de .\n',
    ":r a aprov:TextReading ; aprov:isReadingOf :titleblock ; aprov:hasReadingOutcome aprov:Empty .\n",
    ':r a aprov:TextReading ; aprov:isReadingOf :page ; aprov:hasReadingOutcome aprov:Failed ; aprov:errorMessage "timeout" .\n',
])
def test_a_reading_with_a_text_or_an_outcome_conforms(body):
    assert check_assertions(body) == []


@pytest.mark.parametrize("body, message", [
    (":r a aprov:TextReading ; aprov:isReadingOf :page .\n", TEXT_OR_OUTCOME),
    (':r a aprov:TextReading ; aprov:isReadingOf :page ; aprov:readText "A" ; aprov:hasReadingOutcome aprov:Empty .\n',
     TEXT_OR_OUTCOME),
    (':r a aprov:TextReading ; aprov:readText "A" .\n', "A reading reads exactly one region or page."),
    (':r a aprov:TextReading ; aprov:isReadingOf :page , :titleblock ; aprov:readText "A" .\n',
     "A reading reads exactly one region or page."),
    (':r a aprov:TextReading ; aprov:isReadingOf :page ; aprov:readText "A" , "B" .\n',
     "A reading has at most one text, a string with or without a language tag."),
    (":r a aprov:TextReading ; aprov:isReadingOf :page ; aprov:readText 42 .\n",
     "A reading has at most one text, a string with or without a language tag."),
    (":r a aprov:TextReading ; aprov:isReadingOf :page ; aprov:hasReadingOutcome aprov:NotPrinted .\n",
     "A reading has at most one outcome: Empty, Illegible or Failed."),
])
def test_a_malformed_reading_is_reported(body, message):
    assert [r["message"] for r in check_assertions(body)] == [message]


# --- the frames a model saw: one resolution, one region, one frame per kept image (#239) ----------------------------------
GEOM = "@prefix geom: <https://w3id.org/adiro/adiro_geometry#> .\n@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .\n"


def check_frames(body):
    graph = Graph().parse(data=PREFIXES + APROV + PROV + GEOM + body, format="turtle")
    return sorted({r["message"] for r in vd.validate(graph, ROOT)})  # a value can break two rules of one message


def test_a_pixel_frame_with_its_resolution_and_a_crop_of_one_region_conform():
    body = """:f300 a geom:CoordinateFrame ; geom:unit "px" ; geom:resolutionDpi 300.0 .
:crop a geom:CoordinateFrame ; geom:unit "px" ; geom:resolutionDpi 300.0 ; geom:coversRegion :box .
:box a geom:BoundingBox .
:image a aprov:DrawingFile ; geom:imageOf :crop ; prov:wasDerivedFrom :pdf .
:pdf a aprov:DrawingFile ; aprov:sourceLocation "https://tile.loc.gov/a.pdf"^^xsd:anyURI .
:pt a geom:CoordinateFrame ; geom:unit "pt" .
"""
    assert check_frames(body) == []


@pytest.mark.parametrize("body, message", [
    (':f a geom:CoordinateFrame ; geom:unit "px" .\n', "A pixel frame (unit px) has a resolutionDpi."),
    (':f a geom:CoordinateFrame ; geom:resolutionDpi 300.0 , 150.0 .\n', "A frame has at most one resolutionDpi, a positive decimal."),
    (':f a geom:CoordinateFrame ; geom:resolutionDpi 0.0 .\n', "A frame has at most one resolutionDpi, a positive decimal."),
    (':f a geom:CoordinateFrame ; geom:resolutionDpi "300" .\n', "A frame has at most one resolutionDpi, a positive decimal."),
    (":f a geom:CoordinateFrame ; geom:coversRegion :a , :b .\n:a a geom:BoundingBox . :b a geom:BoundingBox .\n",
     "A frame covers at most one region, a BoundingBox."),
    (':i a aprov:DrawingFile ; geom:imageOf :f , :g ; aprov:sourceLocation "https://tile.loc.gov/a.png"^^xsd:anyURI .\n:f a geom:CoordinateFrame . :g a geom:CoordinateFrame .\n',
     "A kept image is an image of exactly one frame."),
])
def test_a_malformed_frame_or_kept_image_is_reported(body, message):
    assert check_frames(body) == [message]


def test_a_relative_storage_location_conforms_but_is_never_released():
    body = (':image a aprov:DrawingFile ; aprov:sourceLocation "https://tile.loc.gov/a.tif"^^xsd:anyURI ;'
            ' aprov:storageLocation "crops/page-1-titleblock.png"^^xsd:anyURI .\n')
    assert check_files(body) == []
    assert [r["path"].rsplit("#", 1)[-1] for r in released(body)] == ["storageLocation"]
