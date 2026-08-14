from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "touchhle")
ORIGINAL = Path(__file__).with_name("apply_touchhle_otamatone_v11.py")
source = ORIGINAL.read_text()

# The broad v11 helper intentionally uses strict replacement checks. UILabel's
# initWithCoder: and initWithFrame: share the same three-line epilogue, so the
# first pass found two matches. For v11 we want the first occurrence there
# (initWithCoder:); keep missing-pattern detection but allow duplicate source
# snippets when replace(..., 1) already makes the intended choice explicit.
source = source.replace(
    '    if count != 1:\n        raise RuntimeError(f"Expected one match in {rel}: {old!r}; found {count}")',
    '    if count < 1:\n        raise RuntimeError(f"Expected at least one match in {rel}: {old!r}; found {count}")',
    1,
)

# objc_classes! requires class methods (+) to precede instance methods (-).
# The first v11 helper inserted -initWithCoder: before UIFont's existing +
# methods, so the macro stopped when it later saw +labelFontSize. Rewrite only
# this helper section: +allocWithZone goes with the class methods, while
# -initWithCoder: is inserted immediately before UIFont's first instance method.
section_start = source.index(
    'replace_once(\n    "src/frameworks/uikit/ui_font.rs",\n    "@implementation UIFont: NSObject'
)
section_end = source.index('for old, new in [', section_start)
font_section = r'''replace_once(
    "src/frameworks/uikit/ui_font.rs",
    "@implementation UIFont: NSObject\n\n// Values are checked against iPhone 3GS, iOS 4.0.1",
    "@implementation UIFont: NSObject\n\n"
    "+ (id)allocWithZone:(NSZonePtr)_zone {\n"
    "    env.objc.alloc_object(this, Box::<UIFontHostObject>::default(), &mut env.mem)\n"
    "}\n\n"
    "// Values are checked against iPhone 3GS, iOS 4.0.1",
)
replace_once(
    "src/frameworks/uikit/ui_font.rs",
    "\n- (CGFloat)ascender {\n",
    "\n- (id)initWithCoder:(id)coder {\n"
    "    let name_key = get_static_str(env, \"UIFontName\");\n"
    "    let name: id = msg![env; coder decodeObjectForKey:name_key];\n"
    "    let size_key = get_static_str(env, \"UIFontPointSize\");\n"
    "    let size: CGFloat = if msg![env; coder containsValueForKey:size_key] {\n"
    "        msg![env; coder decodeFloatForKey:size_key]\n"
    "    } else { 14.0 };\n"
    "    let traits_key = get_static_str(env, \"UIFontTraits\");\n"
    "    let traits: i32 = if msg![env; coder containsValueForKey:traits_key] {\n"
    "        msg![env; coder decodeIntForKey:traits_key]\n"
    "    } else { 0 };\n"
    "    let kind = if name != nil {\n"
    "        let name = to_rust_string(env, name);\n"
    "        get_equivalent_font(&name).unwrap_or(if (traits & 2) != 0 { FontKind::SansBold } else { FontKind::SansRegular })\n"
    "    } else if (traits & 2) != 0 {\n"
    "        FontKind::SansBold\n"
    "    } else {\n"
    "        FontKind::SansRegular\n"
    "    };\n"
    "    *env.objc.borrow_mut::<UIFontHostObject>(this) = UIFontHostObject {\n"
    "        size: if size > 0.0 { size } else { 14.0 }, kind\n"
    "    };\n"
    "    this\n"
    "}\n\n"
    "- (CGFloat)ascender {\n",
)
'''
source = source[:section_start] + font_section + source[section_end:]

# Use a temporary sibling so __file__-relative chaining to v10 still works.
tmp = Path(__file__).with_name("_generated_apply_touchhle_otamatone_v11.py")
tmp.write_text(source)
try:
    subprocess.run([sys.executable, str(tmp), str(ROOT)], check=True)
finally:
    tmp.unlink(missing_ok=True)

print("Applied corrected Otamatone v11 comprehensive compatibility helper")
