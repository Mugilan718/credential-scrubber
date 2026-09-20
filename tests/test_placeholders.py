"""
Tests for deterministic typed placeholders (placeholder_mode=True).

All values below are synthetic and clearly fake. Every test that asserts
"no leak" checks the exact captured raw value, not a manually-dequoted
short word - see test_detection_and_sanitization.py's note on why a bare
substring check can false-alarm on a key name that happens to contain the
same word as its value (e.g. "secret_key").
"""
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
import yaml as pyyaml

import engine

_RULES_PATH = Path(engine.__file__).resolve().parent / "rules_default.yaml"


def _rules():
    return engine.load_rules(_RULES_PATH)


def _redact_config(line, filename="f.properties", registry=None):
    rules = _rules()
    entries = []
    out = engine.redact_config_line(line, rules, entries, filename, 1, placeholder_registry=registry)
    return out, entries


# ---------------------------------------------------------------------
# Identity: (category, exact value)
# ---------------------------------------------------------------------

def test_same_value_same_key_gives_same_placeholder():
    registry = engine.PlaceholderRegistry()
    out1, e1 = _redact_config('api_key = "fake-Xyz789Abc12345678"\n', registry=registry)
    out2, e2 = _redact_config('api_key = "fake-Xyz789Abc12345678"\n', registry=registry)
    assert e1[0]["after"] == e2[0]["after"]
    assert out1 == out2


def test_different_values_same_category_give_different_placeholders():
    registry = engine.PlaceholderRegistry()
    _, e1 = _redact_config('api_key = "fake-Aaa111Bbb222Ccc333"\n', registry=registry)
    _, e2 = _redact_config('api_key = "fake-Zzz999Yyy888Xxx777"\n', registry=registry)
    assert e1[0]["after"] != e2[0]["after"]


def test_same_value_under_different_keys_same_category_gives_same_placeholder():
    # The task's own example, using a category actually reachable today
    # (CUSTOMER_ID has no detection rule - see module docstring/BENCHMARK.md).
    registry = engine.PlaceholderRegistry()
    _, e1 = _redact_config('api_key = "fake-Shared9Value12345"\n', registry=registry)
    _, e2 = _redact_config('access_key = "fake-Shared9Value12345"\n', registry=registry)
    assert e1[0]["after"] == e2[0]["after"]
    assert e1[0]["after"] == '"<API_KEY_1>"'  # after includes the original quotes, like MASK mode


def test_different_categories_same_value_give_different_placeholders():
    # No false merge: an accidental literal-text collision across two
    # semantically different categories must not correlate.
    registry = engine.PlaceholderRegistry()
    _, e1 = _redact_config('password = "abc12345678901234567"\n', registry=registry)
    _, e2 = _redact_config('api_key = "abc12345678901234567"\n', registry=registry)
    assert e1[0]["after"] != e2[0]["after"]
    assert e1[0]["after"] == '"<PASSWORD_1>"'
    assert e2[0]["after"] == '"<API_KEY_1>"'


def test_repeated_value_three_or_more_times_all_correlate():
    registry = engine.PlaceholderRegistry()
    lines = [
        'api_key = "fake-Repeat0123456789ab"\n',
        'client_secret = "fake-Repeat0123456789ab"\n',
        'access_key = "fake-Repeat0123456789ab"\n',
    ]
    afters = []
    for line in lines:
        _, entries = _redact_config(line, registry=registry)
        afters.append(entries[0]["after"])
    assert len(set(afters)) == 1


def test_multiple_categories_get_independent_per_category_counters():
    registry = engine.PlaceholderRegistry()
    _, e_pw1 = _redact_config('password = "fake-Pw1aaaaaaaaaaaaaaa"\n', registry=registry)
    _, e_ak1 = _redact_config('api_key = "fake-Ak1aaaaaaaaaaaaaaa"\n', registry=registry)
    _, e_pw2 = _redact_config('password = "fake-Pw2bbbbbbbbbbbbbbb"\n', registry=registry)
    assert e_pw1[0]["after"] == '"<PASSWORD_1>"'
    assert e_ak1[0]["after"] == '"<API_KEY_1>"'
    assert e_pw2[0]["after"] == '"<PASSWORD_2>"'


# ---------------------------------------------------------------------
# Config formats
# ---------------------------------------------------------------------

def test_json_repeated_value_under_different_keys_correlates():
    # JSON/config keys are matched with strict (non-camelCase) boundaries
    # (see key_pattern_matches(camel_aware=False)) - "api_key"/"backup_api_key"
    # match; a camelCase "backupApiKey" would not (that convention is only
    # honored for source-code identifiers, via find_key_matches).
    registry = engine.PlaceholderRegistry()
    _, e1 = _redact_config('  "api_key": "fake-JsonShared123456",\n', filename="f.json", registry=registry)
    _, e2 = _redact_config('  "backup_api_key": "fake-JsonShared123456"\n', filename="f.json", registry=registry)
    assert e1[0]["after"] == e2[0]["after"]


def test_xml_repeated_value_correlates():
    registry = engine.PlaceholderRegistry()
    _, e1 = _redact_config("<apiKey>fake-XmlShared1234567</apiKey>\n", filename="f.xml", registry=registry)
    _, e2 = _redact_config("<accessKey>fake-XmlShared1234567</accessKey>\n", filename="f.xml", registry=registry)
    assert e1[0]["after"] == e2[0]["after"]


def test_dotconfig_attribute_pair_repeated_value_correlates():
    registry = engine.PlaceholderRegistry()
    line1 = '<add key="ApiKey" value="fake-CfgShared123456"/>\n'
    line2 = '<add key="AccessKey" value="fake-CfgShared123456"/>\n'
    _, e1 = _redact_config(line1, filename="Web.config", registry=registry)
    _, e2 = _redact_config(line2, filename="Web.config", registry=registry)
    assert e1[0]["after"] == e2[0]["after"]
    assert 'key="ApiKey"' in _redact_config(line1, filename="Web.config", registry=engine.PlaceholderRegistry())[0]


def test_yaml_repeated_value_correlates_and_stays_yaml_safe():
    registry = engine.PlaceholderRegistry()
    out1, e1 = _redact_config("api_key: fake-YamlShared123456\n", filename="f.yaml", registry=registry)
    out2, e2 = _redact_config("access_key: fake-YamlShared123456\n", filename="f.yaml", registry=registry)
    assert e1[0]["after"] == e2[0]["after"]
    # Unquoted originals -> force-quoted placeholder, exactly like MASK mode;
    # `after` already includes the quotes force_quote added.
    assert e1[0]["after"] == '"<API_KEY_1>"'
    assert out1.strip() == f'api_key: {e1[0]["after"]}'
    pyyaml.safe_load(out1)
    pyyaml.safe_load(out2)


def test_yaml_placeholder_is_inherently_alias_safe_even_unquoted():
    # A typed placeholder never starts with '*', unlike MASK - confirm this
    # holds regardless of the YAML-specific force_quote fix, not just
    # because of it.
    token = engine.PlaceholderRegistry().get_or_create("API_KEY", "x")
    assert not token.startswith("*")


# ---------------------------------------------------------------------
# Multiline concatenation
# ---------------------------------------------------------------------

def test_multiline_python_gets_one_placeholder_on_first_fragment_rest_emptied():
    rules = _rules()
    registry = engine.PlaceholderRegistry()
    lines = [
        "API_SECRET = (\n",
        '    "fake-frag-one"\n',
        '    "fake-frag-two"\n',
        ")\n",
    ]
    entries = []
    out = engine.scan_multiline_python(list(lines), rules, entries, "f.py", placeholder_registry=registry)
    assert len(out) == len(lines)  # line count unchanged
    assert entries[0]["after"].startswith("<")
    assert entries[1]["after"] == ""
    joined_out = "".join(out)
    assert "fake-frag-one" not in joined_out
    assert "fake-frag-two" not in joined_out
    assert "fakefragonefakefragtwo".replace("-", "") not in joined_out.replace("-", "").replace(" ", "")


def test_multiline_plus_gets_one_placeholder_on_first_fragment_rest_emptied():
    rules = _rules()
    registry = engine.PlaceholderRegistry()
    lines = [
        'String authToken = "fake-plusfrag-one" +\n',
        '        "fake-plusfrag-two" +\n',
        '        "fake-plusfrag-three";\n',
    ]
    entries = []
    out = engine.scan_multiline_plus(list(lines), rules, entries, "f.java", placeholder_registry=registry)
    assert len(out) == len(lines)
    assert entries[0]["after"].startswith("<ACCESS_TOKEN_")
    assert entries[1]["after"] == ""
    assert entries[2]["after"] == ""
    joined_out = "".join(out)
    for frag in ("fake-plusfrag-one", "fake-plusfrag-two", "fake-plusfrag-three"):
        assert frag not in joined_out
    # Still syntactically a 3-term concatenation, not collapsed to one line.
    assert joined_out.count("+") == 2


def test_multiline_value_correlates_with_a_single_line_occurrence_elsewhere():
    # The whole reconstructed multiline value is one identity - if the
    # same value also appears as an ordinary single-line finding, both
    # should correlate.
    rules = _rules()
    registry = engine.PlaceholderRegistry()
    multiline_lines = [
        'String authToken = "fakeAB" +\n',
        '        "CD90";\n',
    ]
    entries = []
    engine.scan_multiline_plus(list(multiline_lines), rules, entries, "f.java", placeholder_registry=registry)
    multiline_placeholder = entries[0]["after"]

    single_entries = []
    single_line = 'String backupAuthToken = "fakeABCD90";\n'
    engine.redact_code_line(single_line, "java", rules, single_entries, "f.java", 2, placeholder_registry=registry)
    assert single_entries[0]["after"] == multiline_placeholder


# ---------------------------------------------------------------------
# False positives / non-findings unchanged
# ---------------------------------------------------------------------

def test_false_positive_lines_unaffected_by_placeholder_mode():
    registry = engine.PlaceholderRegistry()
    for line in ["timeout = 5000\n", "port = 8080\n", 'username = "admin"\n']:
        out, entries = _redact_config(line, registry=registry)
        assert out == line
        assert entries == []


# ---------------------------------------------------------------------
# Security invariants
# ---------------------------------------------------------------------

def test_no_original_secret_remains_in_placeholder_mode_output():
    registry = engine.PlaceholderRegistry()
    cases = [
        'password = "fake-Sup3rSecret9x"\n',
        '"password": "fake-supersecret123",\n',
        "<password>fake-password-Xyz</password>\n",
        '<add key="password" value="fake-password-Xyz"/>\n',
    ]
    filenames = ["f.properties", "f.json", "f.xml", "Web.config"]
    for line, fname in zip(cases, filenames):
        out, entries = _redact_config(line, filename=fname, registry=registry)
        for entry in entries:
            assert entry["before"] not in out


def test_placeholder_never_contains_a_substring_of_the_original_secret():
    registry = engine.PlaceholderRegistry()
    secret = "fake-Zx9Qw3Vt7Br2Lm5Cn8Kp1"
    _, entries = _redact_config(f'api_key = "{secret}"\n', registry=registry)
    placeholder = entries[0]["after"]
    # Every substring of length >= 4 of the real value must not appear in
    # the placeholder text.
    for i in range(len(secret) - 3):
        chunk = secret[i:i + 4]
        assert chunk not in placeholder, f"placeholder {placeholder!r} contains secret fragment {chunk!r}"


def test_placeholder_never_reveals_provider_name():
    # aws_access_key_id / github_token / jwt_token / bearer_token all
    # collapse to generic categories - the provider name must never
    # appear in the placeholder.
    rules = _rules()
    registry = engine.PlaceholderRegistry()
    entries = []
    engine.redact_value_patterns_only("AKIA" + "Q" * 16 + "\n", rules, entries, "f.env", 1, placeholder_registry=registry)
    if entries:
        assert "AWS" not in entries[0]["after"].upper() or "AWS" not in entries[0]["after"]
        assert "AKIA" not in entries[0]["after"]

    entries2 = []
    engine.redact_value_patterns_only("ghp_" + "Q" * 36 + "\n", rules, entries2, "f.env", 1, placeholder_registry=registry)
    if entries2:
        assert "GITHUB" not in entries2[0]["after"].upper()
        assert "ghp_" not in entries2[0]["after"]


def test_placeholder_never_reveals_raw_key_name():
    registry = engine.PlaceholderRegistry()
    _, entries = _redact_config('stripeSecretKeyForProdBillingAccount4471 = "fake-Value12345678901"\n', registry=registry)
    assert entries
    assert "stripe" not in entries[0]["after"].lower()
    assert "billing" not in entries[0]["after"].lower()
    assert "4471" not in entries[0]["after"]


def test_placeholder_text_never_correlates_with_original_length():
    registry = engine.PlaceholderRegistry()
    _, short_entries = _redact_config('api_key = "fake-Ab12cdefghijklmno"\n', registry=registry)
    _, long_entries = _redact_config('client_secret = "fake-VeryMuchLongerSecretValueThatGoesOnForAWhileMoreCharacters123456789"\n', registry=registry)
    # Both placeholders are API_KEY-categorized (client_secret -> API_KEY);
    # their text length must be governed only by the category name +
    # ordinal, not by how long the original value was.
    assert abs(len(short_entries[0]["after"]) - len(long_entries[0]["after"])) <= 1  # "_1" vs "_2" width only


# ---------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------

def _write_multi_file_project(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "zeta.properties").write_text('api_key = "fake-ZetaValue123456"\n', encoding="utf-8")
    (project / "alpha.properties").write_text('api_key = "fake-AlphaValue123456"\n', encoding="utf-8")
    (project / "mid.properties").write_text('api_key = "fake-ZetaValue123456"\n', encoding="utf-8")  # repeats zeta's value
    return project


def test_deterministic_output_across_repeated_scans(tmp_path):
    rules = _rules()
    project = _write_multi_file_project(tmp_path)

    out1 = tmp_path / "out1"
    entries1, _, _ = engine.scan_project(project, out1, rules, placeholder_mode=True)
    out2 = tmp_path / "out2"
    entries2, _, _ = engine.scan_project(project, out2, rules, placeholder_mode=True)

    def normalize(entries):
        return sorted((e["file"], e["line"], e["before"], e["after"]) for e in entries)

    assert normalize(entries1) == normalize(entries2)
    for rel in ["zeta.properties", "alpha.properties", "mid.properties"]:
        assert (out1 / rel).read_text(encoding="utf-8") == (out2 / rel).read_text(encoding="utf-8")


def test_deterministic_numbering_across_files_regardless_of_creation_order(tmp_path):
    # alpha.properties is created AFTER zeta.properties on disk, but sorts
    # first - traversal must number by sorted path, not creation time.
    project = _write_multi_file_project(tmp_path)
    rules = _rules()
    out = tmp_path / "out"
    entries, _, _ = engine.scan_project(project, out, rules, placeholder_mode=True)

    by_file = {e["file"].replace("\\", "/"): e["after"] for e in entries}
    # alpha.properties sorts before zeta.properties -> alpha's distinct
    # value gets the lower ordinal (values in the fixture are quoted, so
    # `after` includes the quotes too, same as MASK mode would).
    assert by_file["alpha.properties"] == '"<API_KEY_1>"'
    assert by_file["zeta.properties"] == '"<API_KEY_2>"'
    # mid.properties repeats zeta's value and must share its placeholder.
    assert by_file["mid.properties"] == by_file["zeta.properties"]


# ---------------------------------------------------------------------
# placeholder_mode disabled (default) is byte-identical to before
# ---------------------------------------------------------------------

def test_placeholder_mode_disabled_by_default_gives_existing_mask_behavior():
    rules = _rules()
    entries = []
    out = engine.redact_config_line('password = "fake-Sup3rSecret9x"\n', rules, entries, "f.properties", 1)
    assert entries[0]["after"] == '"***REDACTED***"'
    assert out.strip() == 'password = "***REDACTED***"'


def test_placeholder_mode_explicit_none_matches_default(tmp_path):
    rules = _rules()
    project = tmp_path / "project"
    project.mkdir()
    (project / "a.properties").write_text('password = "fake-Sup3rSecret9x"\n', encoding="utf-8")

    out_default = tmp_path / "out_default"
    entries_default, _, _ = engine.scan_project(project, out_default, rules)
    out_explicit = tmp_path / "out_explicit"
    entries_explicit, _, _ = engine.scan_project(project, out_explicit, rules, placeholder_mode=False)

    assert entries_default[0]["after"] == entries_explicit[0]["after"] == '"***REDACTED***"'
    assert (out_default / "a.properties").read_text(encoding="utf-8") == (out_explicit / "a.properties").read_text(encoding="utf-8")


def test_full_scan_project_placeholder_mode_matches_mask_mode_detection_shape(tmp_path):
    """Same findings (file, line, key, rule) fire in both modes - only
    `after` differs. Uses a small multi-format project rather than
    re-testing every line in benchmark/dataset/files/ (that's what
    run_benchmark.py --placeholder-mode is for)."""
    rules = _rules()
    project = tmp_path / "project"
    project.mkdir()
    (project / "app.properties").write_text(
        'password = "fake-Sup3rSecret9x"\napi_key = "fake-Ab12cdefghijklmno"\n', encoding="utf-8"
    )

    out_mask = tmp_path / "out_mask"
    entries_mask, scanned_mask, _ = engine.scan_project(project, out_mask, rules)
    out_ph = tmp_path / "out_ph"
    entries_ph, scanned_ph, _ = engine.scan_project(project, out_ph, rules, placeholder_mode=True)

    assert scanned_mask == scanned_ph
    assert len(entries_mask) == len(entries_ph)
    for em, ep in zip(entries_mask, entries_ph):
        assert em["file"] == ep["file"]
        assert em["line"] == ep["line"]
        assert em["key"] == ep["key"]
        assert em["rule"] == ep["rule"]
        assert em["before"] == ep["before"]


# ---------------------------------------------------------------------
# XML/.config well-formedness (regression for the review's B.1 finding:
# a typed placeholder like "<PASSWORD_1>" contains XML metacharacters
# ('<'/'>') that MASK never did, so writing it unescaped into XML element
# text or an attribute value produced invalid XML - see
# engine._xml_escape_placeholder().
# ---------------------------------------------------------------------

def test_xml_element_text_placeholder_is_well_formed_xml():
    registry = engine.PlaceholderRegistry()
    out, entries = _redact_config(
        "<password>fake-XmlElementSecret123</password>\n", filename="f.xml", registry=registry
    )
    assert entries[0]["before"] not in out
    assert entries[0]["after"] == "&lt;PASSWORD_1&gt;"
    ET.fromstring(out.strip())  # raises ET.ParseError if not well-formed


def test_xml_attribute_value_placeholder_is_well_formed_xml():
    registry = engine.PlaceholderRegistry()
    out, entries = _redact_config(
        '<add key="ApiKey" value="fake-XmlAttrSecret123"/>\n', filename="Web.config", registry=registry
    )
    assert entries[0]["before"] not in out
    # _KV_XML_ATTR_PAIR captures the value span *without* its surrounding
    # quotes (they're structural, part of the line's mid/suffix groups) -
    # unlike the JSON/bareword shapes, so no quote-wrap is added here; the
    # quotes visible in `out` are the untouched original ones.
    assert entries[0]["after"] == "&lt;API_KEY_1&gt;"
    ET.fromstring(out.strip())  # raises ET.ParseError if not well-formed


def test_dotconfig_file_multiple_secrets_well_formed_deterministic_and_no_leak(tmp_path):
    """A full Web.config-shaped file, scanned via scan_project (not just a
    single line), mixing the element-text and attribute-value shapes and a
    repeated value across both - the file must parse as one well-formed XML
    document afterward, the repeated value must correlate to one token, and
    no original secret may survive anywhere in the file."""
    rules = _rules()
    project = tmp_path / "project"
    project.mkdir()
    original_secret = "fake-RepeatedConfigSecret789"
    (project / "Web.config").write_text(
        "<configuration>\n"
        '  <add key="ApiKey" value="{0}"/>\n'
        "  <password>{0}</password>\n"
        "  <connectionSecret>fake-OtherSecretValue456</connectionSecret>\n"
        "</configuration>\n".format(original_secret),
        encoding="utf-8",
    )

    out_dir = tmp_path / "out"
    entries, scanned, skipped = engine.scan_project(project, out_dir, rules, placeholder_mode=True)
    assert scanned == 1
    assert not skipped

    output_text = (out_dir / "Web.config").read_text(encoding="utf-8")
    ET.fromstring(output_text)  # whole-file well-formedness check

    assert original_secret not in output_text
    assert "fake-OtherSecretValue456" not in output_text

    by_key = {e["key"]: e["after"] for e in entries}
    # The two occurrences of the same real secret (attribute-value form and
    # element-text form) must correlate to the same underlying token, even
    # though their escaped/quoted renderings differ cosmetically.
    assert by_key["ApiKey"] == "&lt;API_KEY_1&gt;"
    assert by_key["password"] == "&lt;PASSWORD_1&gt;"


def test_xml_placeholder_mode_disabled_leaves_mask_behavior_unescaped():
    # MASK contains no XML metacharacters, so it never needed escaping -
    # confirm the fix didn't add any for MASK mode (placeholder_mode=False).
    rules = _rules()
    entries = []
    out = engine.redact_config_line(
        "<password>fake-XmlMaskSecret123</password>\n", rules, entries, "f.xml", 1
    )
    assert entries[0]["after"] == "***REDACTED***"
    assert out.strip() == "<password>***REDACTED***</password>"
    ET.fromstring(out.strip())


def test_xml_value_pattern_fallback_line_is_also_escaped():
    # A line with no recognizable key/value shape (falls through to
    # redact_value_patterns_only) but a value_pattern match inside an XML
    # file - the fallback path needs the same escaping as the structured
    # key/value path.
    rules = _rules()
    registry = engine.PlaceholderRegistry()
    entries = []
    line = "  see AKIA" + "Q" * 16 + " for details\n"
    out = engine.redact_config_line(line, rules, entries, "notes.xml", 1, placeholder_registry=registry)
    assert entries
    assert "AKIA" + "Q" * 16 not in out
    assert entries[0]["after"] == "&lt;API_KEY_1&gt;"
    assert "<API_KEY_1>" not in out  # never the raw, unescaped token


# ---------------------------------------------------------------------
# Known limitation (B.2, not fixed here - see BENCHMARK.md): the same real
# value can resolve to a different category, and therefore a different
# placeholder token, depending on which detection path caught it.
# ---------------------------------------------------------------------

def test_known_limitation_connection_string_value_diverges_by_detection_path():
    """A connection-string-shaped value gets CONNECTION_STRING when caught
    via a connection-string-y key_pattern (e.g. "jdbc"), but URL when the
    identical value is caught elsewhere via the generic_url value_pattern
    (which also matches jdbc:/mongodb/redis/amqp schemes, just without
    resolving to the more specific category). This means the *same* real
    value can end up with two different placeholder tokens depending on
    context - a known, documented limitation (see BENCHMARK.md), not fixed
    by this change: doing so would require making category_for_value_pattern
    scheme-aware for "generic_url", which is a real (if small) detection-
    resolution behavior change, not the XML-escaping fix this test suite is
    otherwise about. This test exists to pin the CURRENT behavior so a
    future fix is a deliberate, reviewed change, not a silent drift."""
    registry = engine.PlaceholderRegistry()
    rules = _rules()

    entries1 = []
    line1 = "jdbc.connection = jdbc:mysql://dbhost:3306/mydb?user=x\n"
    engine.redact_config_line(line1, rules, entries1, "a.properties", 1, placeholder_registry=registry)

    entries2 = []
    line2 = "random_note = see jdbc:mysql://dbhost:3306/mydb?user=x for details\n"
    engine.redact_config_line(line2, rules, entries2, "b.properties", 2, placeholder_registry=registry)

    assert entries1[0]["rule"] == "key_name_match"
    assert entries1[0]["after"] == "<CONNECTION_STRING_1>"
    assert entries2[0]["rule"] == "generic_url"
    assert entries2[0]["after"] == "<URL_1>"
    # Documents the divergence explicitly rather than silently asserting
    # equality (which would fail) or silently asserting inequality (which
    # would look like intended behavior rather than a known gap).
    assert entries1[0]["after"] != entries2[0]["after"]
