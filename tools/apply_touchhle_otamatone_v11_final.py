from pathlib import Path
import subprocess
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "touchhle")
HELPER = Path(__file__).with_name("apply_touchhle_otamatone_v11_full.py")
subprocess.run([sys.executable, str(HELPER), str(ROOT)], check=True)


def replace_once(rel, old, new):
    p = ROOT / rel
    s = p.read_text()
    count = s.count(old)
    if count != 1:
        raise RuntimeError(f"Expected one match in {rel}: {old!r}; found {count}")
    p.write_text(s.replace(old, new, 1))


# v11's broad helper matched the common `addSubview:text_label; this` epilogue
# in initWithFrame: first. Move the NSCoder-specific property decoding to the
# actual initWithCoder: method.
text_field = ROOT / "src/frameworks/uikit/ui_view/ui_control/ui_text_field.rs"
s = text_field.read_text()
decode = '''    let key = ns_string::get_static_str(env, "UIText");
    let text: id = msg![env; coder decodeObjectForKey:key];
    if text != nil {
        () = msg![env; this setText:text];
    }
    let key = ns_string::get_static_str(env, "UITextColor");
    let color: id = msg![env; coder decodeObjectForKey:key];
    if color != nil {
        () = msg![env; this setTextColor:color];
    }
    let key = ns_string::get_static_str(env, "UIFont");
    let font: id = msg![env; coder decodeObjectForKey:key];
    if font != nil {
        () = msg![env; this setFont:font];
    }
'''
if s.count(decode) != 1:
    raise RuntimeError(f"Expected misplaced UITextField decode block once; found {s.count(decode)}")
s = s.replace(decode, "", 1)
marker = '''- (id)initWithCoder:(id)coder {
    let this: id = msg_super![env; this initWithCoder: coder];

    // TODO: actual decoding of properties

    let text_label: id = msg_class![env; UILabel new];

    let host_obj = env.objc.borrow_mut::<UITextFieldHostObject>(this);
    host_obj.text_label = text_label;

    () = msg![env; this addSubview:text_label];

    this
}'''
replacement = '''- (id)initWithCoder:(id)coder {
    let this: id = msg_super![env; this initWithCoder: coder];

    let text_label: id = msg_class![env; UILabel new];
    let host_obj = env.objc.borrow_mut::<UITextFieldHostObject>(this);
    host_obj.text_label = text_label;
    () = msg![env; this addSubview:text_label];

''' + decode + '''
    this
}'''
if s.count(marker) != 1:
    raise RuntimeError(f"Expected UITextField initWithCoder marker once; found {s.count(marker)}")
text_field.write_text(s.replace(marker, replacement, 1))

# Do not keep an immutable HostObject borrow alive while release() mutably
# borrows the Objective-C runtime.
replace_once(
    "src/frameworks/uikit/ui_view/ui_web_view.rs",
    "- (())dealloc {\n    let h = env.objc.borrow::<UIWebViewHostObject>(this);\n    release(env, h.request);\n    release(env, h.content_label);\n    msg_super![env; this dealloc]\n}",
    "- (())dealloc {\n"
    "    let (request, content_label) = {\n"
    "        let h = env.objc.borrow::<UIWebViewHostObject>(this);\n"
    "        (h.request, h.content_label)\n"
    "    };\n"
    "    release(env, request);\n"
    "    release(env, content_label);\n"
    "    msg_super![env; this dealloc]\n"
    "}",
)

print("Applied final Otamatone v11 compile fixes")
