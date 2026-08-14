from pathlib import Path
import subprocess
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "touchhle")
HELPER = Path(__file__).with_name("apply_touchhle_otamatone_v2.py")

# Keep all compatibility fixes from v2 first.
subprocess.run([sys.executable, str(HELPER), str(ROOT)], check=True)


def replace_once(rel, old, new):
    p = ROOT / rel
    s = p.read_text()
    count = s.count(old)
    if count != 1:
        raise RuntimeError(f"Expected one match in {rel}: {old!r}; found {count}")
    p.write_text(s.replace(old, new, 1))


# v2's full ABI/dyld trace is intentionally very noisy and substantially slows
# old NIB-heavy apps. v3 goes back to normal logging and adds a precise tracer
# around guest implementations of -initWithCoder:, which is where the v2 log
# ended without returning.
replace_once(
    "src/log.rs",
    'pub const ENABLED_MODULES: &[&str] = &["touchHLE::abi", "touchHLE::dyld"];',
    'pub const ENABLED_MODULES: &[&str] = &[];',
)

replace_once(
    "src/objc/messages.rs",
    "                    IMP::Guest(guest_imp) => guest_imp.call_without_pushing_stack_frame(env),\n",
    "                    IMP::Guest(guest_imp) => {\n"
    "                        let guest_imp = *guest_imp;\n"
    "                        let selector_name = selector.as_str(&env.mem).to_string();\n"
    "                        if selector_name == \"initWithCoder:\" {\n"
    "                            let class_name = name.clone();\n"
    "                            log!(\n"
    "                                \"Otamatone trace: ENTER guest -[{} {}] receiver={:?} imp={:?}\",\n"
    "                                class_name, selector_name, receiver, guest_imp\n"
    "                            );\n"
    "                            guest_imp.call_without_pushing_stack_frame(env);\n"
    "                            log!(\n"
    "                                \"Otamatone trace: EXIT  guest -[{} {}] receiver={:?} imp={:?}\",\n"
    "                                class_name, selector_name, receiver, guest_imp\n"
    "                            );\n"
    "                        } else {\n"
    "                            guest_imp.call_without_pushing_stack_frame(env);\n"
    "                        }\n"
    "                    }\n",
)

print("Applied Otamatone v3 targeted initWithCoder tracer")
