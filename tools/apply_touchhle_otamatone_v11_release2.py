from pathlib import Path
import subprocess
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "touchhle")
HELPER = Path(__file__).with_name("apply_touchhle_otamatone_v11_full.py")
subprocess.run([sys.executable, str(HELPER), str(ROOT)], check=True)

# ---------------------------------------------------------------------------
# UITextField: the broad helper's compact decoder was inserted into the first
# matching init epilogue (initWithFrame). Move it structurally into
# initWithCoder without depending on rustfmt output.
# ---------------------------------------------------------------------------
p = ROOT / "src/frameworks/uikit/ui_view/ui_control/ui_text_field.rs"
s = p.read_text()
compact_decode = (
    '    let key = ns_string::get_static_str(env, "UIText"); let text: id = msg![env; coder decodeObjectForKey:key]; if text != nil { () = msg![env; this setText:text]; }\n'
    '    let key = ns_string::get_static_str(env, "UITextColor"); let color: id = msg![env; coder decodeObjectForKey:key]; if color != nil { () = msg![env; this setTextColor:color]; }\n'
    '    let key = ns_string::get_static_str(env, "UIFont"); let font: id = msg![env; coder decodeObjectForKey:key]; if font != nil { () = msg![env; this setFont:font]; }\n'
)
if s.count(compact_decode) != 1:
    raise RuntimeError(f"Expected compact misplaced UITextField decoder once; found {s.count(compact_decode)}")
s = s.replace(compact_decode, "", 1)

method_start = s.index("- (id)initWithCoder:(id)coder {")
method_end = s.index("\n}\n\n- (())dealloc", method_start)
method = s[method_start:method_end]
insert_at = method.rfind("    this")
if insert_at < 0:
    raise RuntimeError("Could not find UITextField initWithCoder return")
decode = '''    let key = ns_string::get_static_str(env, "UIText");
    let text: id = msg![env; coder decodeObjectForKey:key];
    if text != nil { () = msg![env; this setText:text]; }
    let key = ns_string::get_static_str(env, "UITextColor");
    let color: id = msg![env; coder decodeObjectForKey:key];
    if color != nil { () = msg![env; this setTextColor:color]; }
    let key = ns_string::get_static_str(env, "UIFont");
    let font: id = msg![env; coder decodeObjectForKey:key];
    if font != nil { () = msg![env; this setFont:font]; }

'''
method = method[:insert_at] + decode + method[insert_at:]
s = s[:method_start] + method + s[method_end:]
p.write_text(s)

# ---------------------------------------------------------------------------
# UIWebView: avoid holding an ObjC host-object borrow across release().
# The generated source is deliberately compact before cargo fmt.
# ---------------------------------------------------------------------------
p = ROOT / "src/frameworks/uikit/ui_view/ui_web_view.rs"
s = p.read_text()
old = '- (())dealloc { let h=env.objc.borrow::<UIWebViewHostObject>(this); release(env,h.request); release(env,h.content_label); msg_super![env; this dealloc] }'
new = '''- (())dealloc {
    let (request, content_label) = {
        let h = env.objc.borrow::<UIWebViewHostObject>(this);
        (h.request, h.content_label)
    };
    release(env, request);
    release(env, content_label);
    msg_super![env; this dealloc]
}'''
if s.count(old) != 1:
    raise RuntimeError(f"Expected compact UIWebView dealloc once; found {s.count(old)}")
p.write_text(s.replace(old, new, 1))

# ---------------------------------------------------------------------------
# Interface Builder First Responder is a semantic nil target, not a concrete
# proxy. This lets UIControl's v11 responder-chain routing handle old archived
# Close/Done/Return actions correctly.
# ---------------------------------------------------------------------------
p = ROOT / "src/frameworks/uikit/ui_nib.rs"
s = p.read_text()
old = '''    } else {
        log!("TODO: UIProxyObject replacement for {}, instance {:?} left unreplaced", id, this);
        this
    }
}'''
new = '''    } else if id == "IBFirstResponder" {
        release(env, this);
        nil
    } else {
        log!("Warning: unknown UIProxyObject {}, instance {:?} left unreplaced", id, this);
        this
    }
}'''
if s.count(old) != 1:
    raise RuntimeError(f"Expected UIProxyObject fallback once; found {s.count(old)}")
p.write_text(s.replace(old, new, 1))

print("Applied rustfmt-independent Otamatone v11 release fixes")
