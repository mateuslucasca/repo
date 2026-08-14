from pathlib import Path
import subprocess
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "touchhle")
HELPER = Path(__file__).with_name("apply_touchhle_otamatone_v10.py")
subprocess.run([sys.executable, str(HELPER), str(ROOT)], check=True)


def replace_once(rel, old, new):
    p = ROOT / rel
    s = p.read_text()
    count = s.count(old)
    if count != 1:
        raise RuntimeError(f"Expected one match in {rel}: {old!r}; found {count}")
    p.write_text(s.replace(old, new, 1))


# ---------------------------------------------------------------------------
# UIView: decode legacy NIB state that touchHLE previously ignored.
# This fixes alpha, touch interception, clipping flags and old autoresize state.
# ---------------------------------------------------------------------------
replace_once(
    "src/frameworks/uikit/ui_view.rs",
    "    multiple_touch_enabled: bool,\n}",
    "    multiple_touch_enabled: bool,\n"
    "    content_mode: NSInteger,\n"
    "    autoresizing_mask: NSUInteger,\n"
    "    autoresizes_subviews: bool,\n"
    "}",
)
replace_once(
    "src/frameworks/uikit/ui_view.rs",
    "            multiple_touch_enabled: false,\n        }",
    "            multiple_touch_enabled: false,\n"
    "            content_mode: 0,\n"
    "            autoresizing_mask: 0,\n"
    "            autoresizes_subviews: true,\n"
    "        }",
)
replace_once(
    "src/frameworks/uikit/ui_view.rs",
    "    () = msg![env; this setMultipleTouchEnabled:multi_touch_enabled];\n\n    for i in 0..subview_count {",
    "    () = msg![env; this setMultipleTouchEnabled:multi_touch_enabled];\n\n"
    "    let key = get_static_str(env, \"UIAlpha\");\n"
    "    if msg![env; coder containsValueForKey:key] {\n"
    "        let alpha: CGFloat = msg![env; coder decodeFloatForKey:key];\n"
    "        () = msg![env; this setAlpha:alpha];\n"
    "    }\n"
    "    let key = get_static_str(env, \"UIUserInteractionDisabled\");\n"
    "    if msg![env; coder containsValueForKey:key] {\n"
    "        let disabled: bool = msg![env; coder decodeBoolForKey:key];\n"
    "        () = msg![env; this setUserInteractionEnabled:(!disabled)];\n"
    "    }\n"
    "    let key = get_static_str(env, \"UIClipsToBounds\");\n"
    "    if msg![env; coder containsValueForKey:key] {\n"
    "        let clips: bool = msg![env; coder decodeBoolForKey:key];\n"
    "        () = msg![env; this setClipsToBounds:clips];\n"
    "    }\n"
    "    let key = get_static_str(env, \"UIContentMode\");\n"
    "    if msg![env; coder containsValueForKey:key] {\n"
    "        let mode: NSInteger = msg![env; coder decodeIntegerForKey:key];\n"
    "        () = msg![env; this setContentMode:mode];\n"
    "    }\n"
    "    let key = get_static_str(env, \"UIAutoresizingMask\");\n"
    "    if msg![env; coder containsValueForKey:key] {\n"
    "        let mask: NSInteger = msg![env; coder decodeIntegerForKey:key];\n"
    "        () = msg![env; this setAutoresizingMask:(mask as NSUInteger)];\n"
    "    }\n"
    "    let key = get_static_str(env, \"UIAutoresizeSubviews\");\n"
    "    if msg![env; coder containsValueForKey:key] {\n"
    "        let enabled: bool = msg![env; coder decodeBoolForKey:key];\n"
    "        () = msg![env; this setAutoresizesSubviews:enabled];\n"
    "    }\n\n"
    "    for i in 0..subview_count {",
)
replace_once(
    "src/frameworks/uikit/ui_view.rs",
    "- (())setClipsToBounds:(bool)clips {\n    todo_objc_setter!(this, clips);\n}",
    "- (bool)clipsToBounds {\n"
    "    let layer = env.objc.borrow::<UIViewHostObject>(this).layer;\n"
    "    msg![env; layer masksToBounds]\n"
    "}\n"
    "- (())setClipsToBounds:(bool)clips {\n"
    "    let layer = env.objc.borrow::<UIViewHostObject>(this).layer;\n"
    "    () = msg![env; layer setMasksToBounds:clips];\n"
    "}",
)
replace_once(
    "src/frameworks/uikit/ui_view.rs",
    "- (())setContentMode:(NSInteger)content_mode { // should be UIViewContentMode\n    todo_objc_setter!(this, content_mode);\n}",
    "- (NSInteger)contentMode {\n"
    "    env.objc.borrow::<UIViewHostObject>(this).content_mode\n"
    "}\n"
    "- (())setContentMode:(NSInteger)content_mode { // should be UIViewContentMode\n"
    "    env.objc.borrow_mut::<UIViewHostObject>(this).content_mode = content_mode;\n"
    "}",
)
replace_once(
    "src/frameworks/uikit/ui_view.rs",
    "- (())setAutoresizingMask:(NSUInteger)mask {\n    todo_objc_setter!(this, mask);\n}\n- (())setAutoresizesSubviews:(bool)enabled {\n    todo_objc_setter!(this, enabled);\n}",
    "- (NSUInteger)autoresizingMask {\n"
    "    env.objc.borrow::<UIViewHostObject>(this).autoresizing_mask\n"
    "}\n"
    "- (())setAutoresizingMask:(NSUInteger)mask {\n"
    "    env.objc.borrow_mut::<UIViewHostObject>(this).autoresizing_mask = mask;\n"
    "}\n"
    "- (bool)autoresizesSubviews {\n"
    "    env.objc.borrow::<UIViewHostObject>(this).autoresizes_subviews\n"
    "}\n"
    "- (())setAutoresizesSubviews:(bool)enabled {\n"
    "    env.objc.borrow_mut::<UIViewHostObject>(this).autoresizes_subviews = enabled;\n"
    "}",
)
replace_once(
    "src/frameworks/uikit/ui_view.rs",
    "        multiple_touch_enabled: _,\n    } = std::mem::take(env.objc.borrow_mut(this));",
    "        multiple_touch_enabled: _,\n"
    "        content_mode: _,\n"
    "        autoresizing_mask: _,\n"
    "        autoresizes_subviews: _,\n"
    "    } = std::mem::take(env.objc.borrow_mut(this));",
)

# CALayer masksToBounds state. The compositor still uses the normal layer tree,
# but storing/forwarding this state fixes UIKit semantics and removes the
# setClipsToBounds stub for legacy custom controls.
replace_once(
    "src/frameworks/core_animation/ca_layer.rs",
    "    pub(super) opaque: bool,\n",
    "    pub(super) opaque: bool,\n    pub(super) masks_to_bounds: bool,\n",
)
replace_once(
    "src/frameworks/core_animation/ca_layer.rs",
    "        opaque: false,\n",
    "        opaque: false,\n        masks_to_bounds: false,\n",
)
replace_once(
    "src/frameworks/core_animation/ca_layer.rs",
    "- (bool)isOpaque {\n",
    "- (bool)masksToBounds {\n"
    "    env.objc.borrow::<CALayerHostObject>(this).masks_to_bounds\n"
    "}\n"
    "- (())setMasksToBounds:(bool)masks {\n"
    "    env.objc.borrow_mut::<CALayerHostObject>(this).masks_to_bounds = masks;\n"
    "}\n\n"
    "- (bool)isOpaque {\n",
)

# ---------------------------------------------------------------------------
# UIControl: NIB state + proper nil target responder-chain routing.
# IBFirstResponder actions in this app depend on standard nil-target behavior.
# ---------------------------------------------------------------------------
replace_once(
    "src/frameworks/uikit/ui_view/ui_control.rs",
    "fn send_actions(env: &mut Environment, this: id, event: id, control_event: UIControlEvents) {",
    "fn resolve_action_target(env: &mut Environment, sender: id, action: SEL) -> id {\n"
    "    let mut candidate = env.framework_state.uikit.ui_responder.first_responder;\n"
    "    if candidate == nil {\n"
    "        candidate = sender;\n"
    "    }\n"
    "    while candidate != nil {\n"
    "        let responds: bool = msg![env; candidate respondsToSelector:action];\n"
    "        if responds {\n"
    "            return candidate;\n"
    "        }\n"
    "        candidate = msg![env; candidate nextResponder];\n"
    "    }\n"
    "    nil\n"
    "}\n\n"
    "fn send_actions(env: &mut Environment, this: id, event: id, control_event: UIControlEvents) {",
)
replace_once(
    "src/frameworks/uikit/ui_view/ui_control.rs",
    "    for (target, action) in action_targets {\n        assert!(target != nil); // TODO\n\n        () = msg![env; this sendAction:action to:target forEvent:event];\n    }",
    "    for (target, action) in action_targets {\n"
    "        () = msg![env; this sendAction:action to:target forEvent:event];\n"
    "    }",
)
replace_once(
    "src/frameworks/uikit/ui_view/ui_control.rs",
    "- (())dealloc {",
    "- (id)initWithCoder:(id)coder {\n"
    "    let this: id = msg_super![env; this initWithCoder:coder];\n"
    "    let key = crate::frameworks::foundation::ns_string::get_static_str(env, \"UIEnabled\");\n"
    "    if msg![env; coder containsValueForKey:key] {\n"
    "        let value: bool = msg![env; coder decodeBoolForKey:key];\n"
    "        () = msg![env; this setEnabled:value];\n"
    "    }\n"
    "    let key = crate::frameworks::foundation::ns_string::get_static_str(env, \"UISelected\");\n"
    "    if msg![env; coder containsValueForKey:key] {\n"
    "        let value: bool = msg![env; coder decodeBoolForKey:key];\n"
    "        () = msg![env; this setSelected:value];\n"
    "    }\n"
    "    let key = crate::frameworks::foundation::ns_string::get_static_str(env, \"UIHighlighted\");\n"
    "    if msg![env; coder containsValueForKey:key] {\n"
    "        let value: bool = msg![env; coder decodeBoolForKey:key];\n"
    "        () = msg![env; this setHighlighted:value];\n"
    "    }\n"
    "    this\n"
    "}\n\n"
    "- (())dealloc {",
)
replace_once(
    "src/frameworks/uikit/ui_view/ui_control.rs",
    "    if target == nil {\n        // TODO: when the target is nil, the responder chain is searched for\n        // a suitable target\n        log!(\n            \"TODO: [{:?} addTarget:nil action:{:?} forControlEvents:{:?}] (ignored)\",\n            target,\n            action,\n            events,\n        );\n        return;\n    }\n    // The target is a *weak* reference!\n",
    "    // The target is a weak reference. nil is meaningful: UIKit resolves\n"
    "    // it through the responder chain when the event is sent.\n",
)
replace_once(
    "src/frameworks/uikit/ui_view/ui_control.rs",
    "    assert!(target != nil); // TODO\n\n    let sel_str = action.as_str(&env.mem);",
    "    let target = if target == nil {\n"
    "        resolve_action_target(env, this, action)\n"
    "    } else {\n"
    "        target\n"
    "    };\n"
    "    if target == nil {\n"
    "        log!(\"Warning: no responder found for control action {:?}\", action);\n"
    "        return;\n"
    "    }\n\n"
    "    let sel_str = action.as_str(&env.mem);",
)

# ---------------------------------------------------------------------------
# Fonts: legacy NIB UIFont decoding and sensible substitutes for app fonts.
# ---------------------------------------------------------------------------
replace_once(
    "src/frameworks/uikit/ui_font.rs",
    "use crate::frameworks::foundation::ns_string::to_rust_string;",
    "use crate::frameworks::foundation::ns_string::{get_static_str, to_rust_string};",
)
replace_once(
    "src/frameworks/uikit/ui_font.rs",
    "use crate::objc::{autorelease, id, msg, objc_classes, ClassExports, HostObject};",
    "use crate::objc::{autorelease, id, msg, nil, objc_classes, ClassExports, HostObject, NSZonePtr};",
)
replace_once(
    "src/frameworks/uikit/ui_font.rs",
    "struct UIFontHostObject {\n    size: CGFloat,\n    kind: FontKind,\n}\nimpl HostObject for UIFontHostObject {}",
    "struct UIFontHostObject {\n"
    "    size: CGFloat,\n"
    "    kind: FontKind,\n"
    "}\n"
    "impl Default for UIFontHostObject {\n"
    "    fn default() -> Self {\n"
    "        Self { size: 14.0, kind: FontKind::SansRegular }\n"
    "    }\n"
    "}\n"
    "impl HostObject for UIFontHostObject {}",
)
replace_once(
    "src/frameworks/uikit/ui_font.rs",
    "@implementation UIFont: NSObject\n\n// Values are checked against iPhone 3GS, iOS 4.0.1",
    "@implementation UIFont: NSObject\n\n"
    "+ (id)allocWithZone:(NSZonePtr)_zone {\n"
    "    env.objc.alloc_object(this, Box::<UIFontHostObject>::default(), &mut env.mem)\n"
    "}\n\n"
    "- (id)initWithCoder:(id)coder {\n"
    "    let name_key = get_static_str(env, \"UIFontName\");\n"
    "    let name: id = msg![env; coder decodeObjectForKey:name_key];\n"
    "    let size_key = get_static_str(env, \"UIFontPointSize\");\n"
    "    let size: CGFloat = msg![env; coder decodeFloatForKey:size_key];\n"
    "    let traits_key = get_static_str(env, \"UIFontTraits\");\n"
    "    let traits: i32 = msg![env; coder decodeIntForKey:traits_key];\n"
    "    let kind = if name != nil {\n"
    "        let name = to_rust_string(env, name);\n"
    "        get_equivalent_font(&name).unwrap_or(if (traits & 2) != 0 { FontKind::SansBold } else { FontKind::SansRegular })\n"
    "    } else if (traits & 2) != 0 {\n"
    "        FontKind::SansBold\n"
    "    } else {\n"
    "        FontKind::SansRegular\n"
    "    };\n"
    "    *env.objc.borrow_mut::<UIFontHostObject>(this) = UIFontHostObject { size: if size > 0.0 { size } else { 14.0 }, kind };\n"
    "    this\n"
    "}\n\n"
    "// Values are checked against iPhone 3GS, iOS 4.0.1",
)
for old, new in [
    ('"HiraKakuProN-W6" => None,', '"HiraKakuProN-W6" => Some(FontKind::SansBold),'),
    ('"HiraKakuProN-W3" => None,', '"HiraKakuProN-W3" => Some(FontKind::SansRegular),'),
    ('"Helvetica" => None,', '"Helvetica" => Some(FontKind::SansRegular),'),
    ('"Helvetica-Bold" => None,', '"Helvetica-Bold" => Some(FontKind::SansBold),'),
    ('"HelveticaNeue" => None,', '"HelveticaNeue" => Some(FontKind::SansRegular),'),
    ('"HelveticaNeue-Bold" => None,', '"HelveticaNeue-Bold" => Some(FontKind::SansBold),'),
]:
    replace_once("src/frameworks/uikit/ui_font.rs", old, new)

# UILabel: honor font/alignment/wrapping/line count and minimum-font flags.
replace_once(
    "src/frameworks/uikit/ui_view/ui_label.rs",
    "    number_of_lines: NSInteger,\n}",
    "    number_of_lines: NSInteger,\n"
    "    minimum_font_size: CGFloat,\n"
    "    adjusts_font_size_to_fit_width: bool,\n"
    "}",
)
replace_once(
    "src/frameworks/uikit/ui_view/ui_label.rs",
    "            number_of_lines: 1,\n        }",
    "            number_of_lines: 1,\n"
    "            minimum_font_size: 0.0,\n"
    "            adjusts_font_size_to_fit_width: false,\n"
    "        }",
)
replace_once(
    "src/frameworks/uikit/ui_view/ui_label.rs",
    "    // TODO: Decode other property values from the coder\n    () = msg![env; this setFont:nil];\n\n    let key_ns_string = get_static_str(env, \"UIText\");",
    "    let key_ns_string = get_static_str(env, \"UIFont\");\n"
    "    let font: id = msg![env; coder decodeObjectForKey:key_ns_string];\n"
    "    () = msg![env; this setFont:font];\n\n"
    "    let key_ns_string = get_static_str(env, \"UIText\");",
)
replace_once(
    "src/frameworks/uikit/ui_view/ui_label.rs",
    "    // Built-in views don't have user-controlled opaqueness.\n    () = msg_super![env; this setOpaque:false];\n    this\n}",
    "    let key = get_static_str(env, \"UITextAlignment\");\n"
    "    if msg![env; coder containsValueForKey:key] {\n"
    "        let value: NSInteger = msg![env; coder decodeIntegerForKey:key];\n"
    "        () = msg![env; this setTextAlignment:value];\n"
    "    }\n"
    "    let key = get_static_str(env, \"UILineBreakMode\");\n"
    "    if msg![env; coder containsValueForKey:key] {\n"
    "        let value: NSInteger = msg![env; coder decodeIntegerForKey:key];\n"
    "        () = msg![env; this setLineBreakMode:value];\n"
    "    }\n"
    "    let key = get_static_str(env, \"UINumberOfLines\");\n"
    "    if msg![env; coder containsValueForKey:key] {\n"
    "        let value: NSInteger = msg![env; coder decodeIntegerForKey:key];\n"
    "        () = msg![env; this setNumberOfLines:value];\n"
    "    }\n"
    "    let key = get_static_str(env, \"UIMinimumFontSize\");\n"
    "    if msg![env; coder containsValueForKey:key] {\n"
    "        let value: CGFloat = msg![env; coder decodeFloatForKey:key];\n"
    "        () = msg![env; this setMinimumFontSize:value];\n"
    "    }\n"
    "    let key = get_static_str(env, \"UIAdjustsFontSizeToFit\");\n"
    "    if msg![env; coder containsValueForKey:key] {\n"
    "        let value: bool = msg![env; coder decodeBoolForKey:key];\n"
    "        () = msg![env; this setAdjustsFontSizeToFitWidth:value];\n"
    "    }\n\n"
    "    // Built-in views don't have user-controlled opaqueness.\n"
    "    () = msg_super![env; this setOpaque:false];\n"
    "    this\n"
    "}",
)
replace_once(
    "src/frameworks/uikit/ui_view/ui_label.rs",
    "        number_of_lines: _,\n    } = env.objc.borrow(this);",
    "        number_of_lines: _,\n"
    "        minimum_font_size: _,\n"
    "        adjusts_font_size_to_fit_width: _,\n"
    "    } = env.objc.borrow(this);",
)
replace_once(
    "src/frameworks/uikit/ui_view/ui_label.rs",
    "- (bool)adjustsFontSizeToFitWidth {\n    false // default value\n}\n- (())setAdjustsFontSizeToFitWidth:(bool)adjusts {\n    assert!(!adjusts); // TODO\n}\n\n- (())setMinimumFontSize:(CGFloat)size {\n    todo_objc_setter!(this, size);\n}",
    "- (bool)adjustsFontSizeToFitWidth {\n"
    "    env.objc.borrow::<UILabelHostObject>(this).adjusts_font_size_to_fit_width\n"
    "}\n"
    "- (())setAdjustsFontSizeToFitWidth:(bool)adjusts {\n"
    "    env.objc.borrow_mut::<UILabelHostObject>(this).adjusts_font_size_to_fit_width = adjusts;\n"
    "}\n\n"
    "- (())setMinimumFontSize:(CGFloat)size {\n"
    "    env.objc.borrow_mut::<UILabelHostObject>(this).minimum_font_size = size;\n"
    "}\n"
    "- (CGFloat)minimumFontSize {\n"
    "    env.objc.borrow::<UILabelHostObject>(this).minimum_font_size\n"
    "}",
)
replace_once(
    "src/frameworks/uikit/ui_view/ui_label.rs",
    "        number_of_lines,\n    } = env.objc.borrow_mut(this);",
    "        number_of_lines,\n"
    "        minimum_font_size: _,\n"
    "        adjusts_font_size_to_fit_width: _,\n"
    "    } = env.objc.borrow_mut(this);",
)

# ---------------------------------------------------------------------------
# UIButton: decode both normal/highlighted image/title/background states.
# Most Otamatone buttons are image-only and were blank before this.
# ---------------------------------------------------------------------------
replace_once(
    "src/frameworks/uikit/ui_view/ui_control/ui_button.rs",
    "use super::{UIControlState, UIControlStateNormal};",
    "use super::{UIControlState, UIControlStateHighlighted, UIControlStateNormal};",
)
replace_once(
    "src/frameworks/uikit/ui_view/ui_control/ui_button.rs",
    "    /// `UIColor*`\n    title_color: id,\n}",
    "    /// `UIColor*`\n"
    "    title_color: id,\n"
    "    /// `UIImage*`\n"
    "    image: id,\n"
    "    /// `UIImage*`\n"
    "    background_image: id,\n"
    "}",
)
replace_once(
    "src/frameworks/uikit/ui_view/ui_control/ui_button.rs",
    "    // It's not entirely clear how the state information is encoded\n    // in this dict.\n    // TODO: support decoding properties of other states\n    let key_idx: id = msg_class![env; NSNumber numberWithLongLong:0i64];\n    let button_content: id = msg![env; dict objectForKey:key_idx];\n\n    let title: id = msg![env; button_content title];\n    if title != nil {\n        log_dbg!(\"UIButton initWithCoder: title {}\", to_rust_string(env, title));\n        () = msg![env; this setTitle:title forState:UIControlStateNormal];\n    }\n\n    let title_color: id = msg![env; button_content titleColor];\n    if title_color != nil {\n        log_dbg!(\"UIButton initWithCoder: title_color {}\", to_rust_string(env, title_color));\n        () = msg![env; this setTitleColor:title_color forState:UIControlStateNormal];\n    }\n\n    // TODO: decode other properties\n    update(env, this);",
    "    for state in [UIControlStateNormal, UIControlStateHighlighted] {\n"
    "        let key_idx: id = msg_class![env; NSNumber numberWithLongLong:(state as i64)];\n"
    "        let button_content: id = msg![env; dict objectForKey:key_idx];\n"
    "        if button_content == nil {\n"
    "            continue;\n"
    "        }\n"
    "        let title: id = msg![env; button_content title];\n"
    "        if title != nil { () = msg![env; this setTitle:title forState:state]; }\n"
    "        let title_color: id = msg![env; button_content titleColor];\n"
    "        if title_color != nil { () = msg![env; this setTitleColor:title_color forState:state]; }\n"
    "        let image: id = msg![env; button_content image];\n"
    "        if image != nil { () = msg![env; this setImage:image forState:state]; }\n"
    "        let background: id = msg![env; button_content backgroundImage];\n"
    "        if background != nil { () = msg![env; this setBackgroundImage:background forState:state]; }\n"
    "    }\n"
    "    let font_key = get_static_str(env, \"UIFont\");\n"
    "    let font: id = msg![env; coder decodeObjectForKey:font_key];\n"
    "    if font != nil { () = msg![env; this setFont:font]; }\n"
    "    update(env, this);",
)
replace_once(
    "src/frameworks/uikit/ui_view/ui_control/ui_button.rs",
    "    () = msg![env; background_image_view setFrame:bounds];\n    () = msg![env; label setFrame:bounds];\n    // TODO: layout for image\n",
    "    let image_view = env.objc.borrow::<UIButtonHostObject>(this).image_view;\n"
    "    () = msg![env; background_image_view setFrame:bounds];\n"
    "    () = msg![env; label setFrame:bounds];\n"
    "    () = msg![env; image_view setFrame:bounds];\n",
)
replace_once(
    "src/frameworks/uikit/ui_view/ui_control/ui_button.rs",
    "    let title_color_key = get_static_str(env, \"UITitleColor\");\n    let title_color: id = msg![env; coder decodeObjectForKey:title_color_key];\n    log_dbg!(\"UIButtonContent: UITitleColor -> {:?}\", title_color);\n\n    // TODO: decode other properties\n\n    retain(env, title);\n    retain(env, title_color);\n    let host_obj = env.objc.borrow_mut::<UIButtonContentHostObject>(this);\n    host_obj.title = title;\n    host_obj.title_color = title_color;",
    "    let title_color_key = get_static_str(env, \"UITitleColor\");\n"
    "    let title_color: id = msg![env; coder decodeObjectForKey:title_color_key];\n"
    "    let image_key = get_static_str(env, \"UIImage\");\n"
    "    let image: id = msg![env; coder decodeObjectForKey:image_key];\n"
    "    let background_key = get_static_str(env, \"UIBackgroundImage\");\n"
    "    let background_image: id = msg![env; coder decodeObjectForKey:background_key];\n\n"
    "    retain(env, title);\n"
    "    retain(env, title_color);\n"
    "    retain(env, image);\n"
    "    retain(env, background_image);\n"
    "    let host_obj = env.objc.borrow_mut::<UIButtonContentHostObject>(this);\n"
    "    host_obj.title = title;\n"
    "    host_obj.title_color = title_color;\n"
    "    host_obj.image = image;\n"
    "    host_obj.background_image = background_image;",
)
replace_once(
    "src/frameworks/uikit/ui_view/ui_control/ui_button.rs",
    "- (id)titleColor {\n    env.objc.borrow::<UIButtonContentHostObject>(this).title_color\n}\n",
    "- (id)titleColor {\n"
    "    env.objc.borrow::<UIButtonContentHostObject>(this).title_color\n"
    "}\n"
    "- (id)image { env.objc.borrow::<UIButtonContentHostObject>(this).image }\n"
    "- (id)backgroundImage { env.objc.borrow::<UIButtonContentHostObject>(this).background_image }\n",
)
replace_once(
    "src/frameworks/uikit/ui_view/ui_control/ui_button.rs",
    "        title,\n        title_color\n    } = env.objc.borrow(this);\n    release(env, title);\n    release(env, title_color);",
    "        title,\n"
    "        title_color,\n"
    "        image,\n"
    "        background_image,\n"
    "    } = env.objc.borrow(this);\n"
    "    release(env, title);\n"
    "    release(env, title_color);\n"
    "    release(env, image);\n"
    "    release(env, background_image);",
)

# ---------------------------------------------------------------------------
# UISegmentedControl: render image segments, selection and ValueChanged events.
# ---------------------------------------------------------------------------
segmented = r'''/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */
//! `UISegmentedControl`.

use super::{send_actions, UIControlEventValueChanged};
use crate::frameworks::core_graphics::{CGPoint, CGRect};
use crate::frameworks::foundation::{ns_string::get_static_str, NSInteger, NSUInteger};
use crate::objc::{
    id, impl_HostObject_with_superclass, msg, msg_class, msg_super, nil, objc_classes, release,
    ClassExports, NSZonePtr,
};

pub struct UISegmentedControlHostObject {
    superclass: super::UIControlHostObject,
    segments: Vec<id>, // weak; UIView already retains them as subviews
    selected_index: NSInteger,
}
impl_HostObject_with_superclass!(UISegmentedControlHostObject);
impl Default for UISegmentedControlHostObject {
    fn default() -> Self {
        Self { superclass: Default::default(), segments: Vec::new(), selected_index: -1 }
    }
}

pub struct UISegmentHostObject {
    superclass: super::UIControlHostObject,
    image_view: id,
}
impl_HostObject_with_superclass!(UISegmentHostObject);
impl Default for UISegmentHostObject {
    fn default() -> Self { Self { superclass: Default::default(), image_view: nil } }
}

pub const CLASSES: ClassExports = objc_classes! {

(env, this, _cmd);

@implementation UISegmentedControl: UIControl

+ (id)allocWithZone:(NSZonePtr)_zone {
    env.objc.alloc_object(this, Box::<UISegmentedControlHostObject>::default(), &mut env.mem)
}

- (id)initWithFrame:(CGRect)frame {
    let this: id = msg_super![env; this initWithFrame:frame];
    this
}

- (id)initWithCoder:(id)coder {
    let this: id = msg_super![env; this initWithCoder:coder];
    let key = get_static_str(env, "UISegments");
    let array: id = msg![env; coder decodeObjectForKey:key];
    let count: NSUInteger = msg![env; array count];
    let mut segments = Vec::new();
    for i in 0..count {
        segments.push(msg![env; array objectAtIndex:i]);
    }
    env.objc.borrow_mut::<UISegmentedControlHostObject>(this).segments = segments;
    let key = get_static_str(env, "UISelectedSegmentIndex");
    let selected: NSInteger = if msg![env; coder containsValueForKey:key] {
        msg![env; coder decodeIntegerForKey:key]
    } else { -1 };
    () = msg![env; this setSelectedSegmentIndex:selected];
    this
}

- (NSUInteger)numberOfSegments {
    env.objc.borrow::<UISegmentedControlHostObject>(this).segments.len() as NSUInteger
}
- (NSInteger)selectedSegmentIndex {
    env.objc.borrow::<UISegmentedControlHostObject>(this).selected_index
}
- (())setSelectedSegmentIndex:(NSInteger)index {
    let segments = env.objc.borrow::<UISegmentedControlHostObject>(this).segments.clone();
    env.objc.borrow_mut::<UISegmentedControlHostObject>(this).selected_index = index;
    for (i, segment) in segments.into_iter().enumerate() {
        () = msg![env; segment setSelected:(index == i as NSInteger)];
    }
}
- (())setImage:(id)image forSegmentAtIndex:(NSUInteger)index {
    let segment = env.objc.borrow::<UISegmentedControlHostObject>(this).segments[index as usize];
    () = msg![env; segment setImage:image];
}

- (())endTrackingWithTouch:(id)touch withEvent:(id)event {
    () = msg_super![env; this endTrackingWithTouch:touch withEvent:event];
    let bounds: CGRect = msg![env; this bounds];
    let point: CGPoint = msg![env; touch locationInView:this];
    let count = env.objc.borrow::<UISegmentedControlHostObject>(this).segments.len();
    if count == 0 || bounds.size.width <= 0.0 { return; }
    let x = (point.x - bounds.origin.x).max(0.0).min(bounds.size.width - f32::EPSILON);
    let index = ((x / bounds.size.width) * count as f32).floor() as NSInteger;
    let old: NSInteger = msg![env; this selectedSegmentIndex];
    if old != index {
        () = msg![env; this setSelectedSegmentIndex:index];
        send_actions(env, this, event, UIControlEventValueChanged);
    }
}

@end

@implementation UISegment: UIControl

+ (id)allocWithZone:(NSZonePtr)_zone {
    env.objc.alloc_object(this, Box::<UISegmentHostObject>::default(), &mut env.mem)
}

- (id)initWithFrame:(CGRect)frame {
    let this: id = msg_super![env; this initWithFrame:frame];
    () = msg![env; this setUserInteractionEnabled:false];
    this
}

- (id)initWithCoder:(id)coder {
    let this: id = msg_super![env; this initWithCoder:coder];
    () = msg![env; this setUserInteractionEnabled:false];
    let key = get_static_str(env, "UISegmentInfo");
    let image: id = msg![env; coder decodeObjectForKey:key];
    let image_view: id = msg_class![env; UIImageView new];
    () = msg![env; image_view setUserInteractionEnabled:false];
    () = msg![env; image_view setImage:image];
    let bounds: CGRect = msg![env; this bounds];
    () = msg![env; image_view setFrame:bounds];
    env.objc.borrow_mut::<UISegmentHostObject>(this).image_view = image_view;
    () = msg![env; this addSubview:image_view];
    this
}

- (())setImage:(id)image {
    let image_view = env.objc.borrow::<UISegmentHostObject>(this).image_view;
    if image_view != nil { () = msg![env; image_view setImage:image]; }
}
- (())setSelected:(bool)selected {
    () = msg_super![env; this setSelected:selected];
    () = msg![env; this setAlpha:(if selected { 1.0f32 } else { 0.72f32 })];
}
- (())layoutSubviews {
    let image_view = env.objc.borrow::<UISegmentHostObject>(this).image_view;
    if image_view != nil {
        let bounds: CGRect = msg![env; this bounds];
        () = msg![env; image_view setFrame:bounds];
    }
}
- (())dealloc {
    let image_view = env.objc.borrow::<UISegmentHostObject>(this).image_view;
    release(env, image_view);
    msg_super![env; this dealloc]
}

@end

};
'''
(ROOT / "src/frameworks/uikit/ui_view/ui_control/ui_segmented_control.rs").write_text(segmented)

# ---------------------------------------------------------------------------
# UISlider: decode real NIB value/range, draw a simple legacy slider and track.
# Exact UISlider instances get default visuals; UICustomSwitch subclasses keep
# their own guest implementation and only reuse the v9 state/image API.
# ---------------------------------------------------------------------------
replace_once(
    "src/frameworks/uikit/ui_view/ui_control/ui_slider.rs",
    "use crate::frameworks::core_graphics::CGRect;",
    "use crate::frameworks::core_graphics::{CGPoint, CGRect, CGSize};\n"
    "use crate::frameworks::foundation::ns_string::get_static_str;\n"
    "use crate::frameworks::uikit::ui_view::ui_control::{send_actions, UIControlEventValueChanged};",
)
replace_once(
    "src/frameworks/uikit/ui_view/ui_control/ui_slider.rs",
    "    maximum_value_image: id,\n}",
    "    maximum_value_image: id,\n"
    "    track_view: id,\n"
    "    fill_view: id,\n"
    "    thumb_view: id,\n"
    "}",
)
replace_once(
    "src/frameworks/uikit/ui_view/ui_control/ui_slider.rs",
    "            maximum_value_image: nil,\n        }",
    "            maximum_value_image: nil,\n"
    "            track_view: nil,\n"
    "            fill_view: nil,\n"
    "            thumb_view: nil,\n"
    "        }",
)
replace_once(
    "src/frameworks/uikit/ui_view/ui_control/ui_slider.rs",
    "fn replace_image(env: &mut Environment, slot: &mut id, image: id) {",
    "fn setup_default_views(env: &mut Environment, this: id) {\n"
    "    let class: crate::objc::Class = msg![env; this class];\n"
    "    let slider_class = env.objc.get_known_class(\"UISlider\", &mut env.mem);\n"
    "    if class != slider_class { return; }\n"
    "    let track: id = msg_class![env; UIView new];\n"
    "    let fill: id = msg_class![env; UIView new];\n"
    "    let thumb: id = msg_class![env; UIView new];\n"
    "    let gray: id = msg_class![env; UIColor lightGrayColor];\n"
    "    let blue: id = msg_class![env; UIColor colorWithRed:0.22f32 green:0.48f32 blue:0.92f32 alpha:1.0f32];\n"
    "    let white: id = msg_class![env; UIColor whiteColor];\n"
    "    () = msg![env; track setBackgroundColor:gray];\n"
    "    () = msg![env; fill setBackgroundColor:blue];\n"
    "    () = msg![env; thumb setBackgroundColor:white];\n"
    "    for v in [track, fill, thumb] { () = msg![env; v setUserInteractionEnabled:false]; () = msg![env; this addSubview:v]; }\n"
    "    let host = env.objc.borrow_mut::<UISliderHostObject>(this);\n"
    "    host.track_view = track; host.fill_view = fill; host.thumb_view = thumb;\n"
    "    () = msg![env; this layoutSubviews];\n"
    "}\n\n"
    "fn replace_image(env: &mut Environment, slot: &mut id, image: id) {",
)
# v9 didn't import msg_class; add it.
replace_once(
    "src/frameworks/uikit/ui_view/ui_control/ui_slider.rs",
    "    id, impl_HostObject_with_superclass, msg, msg_super, nil, objc_classes, release, retain,",
    "    id, impl_HostObject_with_superclass, msg, msg_class, msg_super, nil, objc_classes, release, retain,",
)
replace_once(
    "src/frameworks/uikit/ui_view/ui_control/ui_slider.rs",
    "    msg_super![env; this initWithFrame:frame]\n}",
    "    let this: id = msg_super![env; this initWithFrame:frame];\n"
    "    setup_default_views(env, this);\n"
    "    this\n"
    "}",
)
replace_once(
    "src/frameworks/uikit/ui_view/ui_control/ui_slider.rs",
    "    log!(\"Otamatone v9: UISlider initWithCoder this={:?} coder={:?}\", this, coder);\n    msg_super![env; this initWithCoder:coder]\n}",
    "    let this: id = msg_super![env; this initWithCoder:coder];\n"
    "    let key = get_static_str(env, \"UIMinValue\");\n"
    "    if msg![env; coder containsValueForKey:key] { let v: f32 = msg![env; coder decodeFloatForKey:key]; () = msg![env; this setMinimumValue:v]; }\n"
    "    let key = get_static_str(env, \"UIMaxValue\");\n"
    "    if msg![env; coder containsValueForKey:key] { let v: f32 = msg![env; coder decodeFloatForKey:key]; () = msg![env; this setMaximumValue:v]; }\n"
    "    let key = get_static_str(env, \"UIValue\");\n"
    "    if msg![env; coder containsValueForKey:key] { let v: f32 = msg![env; coder decodeFloatForKey:key]; () = msg![env; this setValue:v]; }\n"
    "    setup_default_views(env, this);\n"
    "    this\n"
    "}",
)
replace_once(
    "src/frameworks/uikit/ui_view/ui_control/ui_slider.rs",
    "        maximum_value_image,\n    } = std::mem::take(env.objc.borrow_mut(this));",
    "        maximum_value_image,\n"
    "        track_view,\n"
    "        fill_view,\n"
    "        thumb_view,\n"
    "    } = std::mem::take(env.objc.borrow_mut(this));",
)
replace_once(
    "src/frameworks/uikit/ui_view/ui_control/ui_slider.rs",
    "    release(env, maximum_value_image);\n    msg_super![env; this dealloc]",
    "    release(env, maximum_value_image);\n"
    "    release(env, track_view); release(env, fill_view); release(env, thumb_view);\n"
    "    msg_super![env; this dealloc]",
)
replace_once(
    "src/frameworks/uikit/ui_view/ui_control/ui_slider.rs",
    "    clamp_value(host);\n}\n- (())setValue:(f32)value animated:(bool)_animated {",
    "    clamp_value(host);\n"
    "    () = msg![env; this layoutSubviews];\n"
    "}\n"
    "- (())setValue:(f32)value animated:(bool)_animated {",
)
replace_once(
    "src/frameworks/uikit/ui_view/ui_control/ui_slider.rs",
    "- (())setMinimumValue:(f32)value {\n    let host = env.objc.borrow_mut::<UISliderHostObject>(this);\n    host.minimum_value = value;\n    clamp_value(host);\n}",
    "- (())setMinimumValue:(f32)value {\n"
    "    let host = env.objc.borrow_mut::<UISliderHostObject>(this);\n"
    "    host.minimum_value = value; clamp_value(host);\n"
    "    () = msg![env; this layoutSubviews];\n"
    "}",
)
replace_once(
    "src/frameworks/uikit/ui_view/ui_control/ui_slider.rs",
    "- (())setMaximumValue:(f32)value {\n    let host = env.objc.borrow_mut::<UISliderHostObject>(this);\n    host.maximum_value = value;\n    clamp_value(host);\n}",
    "- (())setMaximumValue:(f32)value {\n"
    "    let host = env.objc.borrow_mut::<UISliderHostObject>(this);\n"
    "    host.maximum_value = value; clamp_value(host);\n"
    "    () = msg![env; this layoutSubviews];\n"
    "}",
)
replace_once(
    "src/frameworks/uikit/ui_view/ui_control/ui_slider.rs",
    "- (())setMinimumValueImage:(id)image {",
    "- (())layoutSubviews {\n"
    "    let host = env.objc.borrow::<UISliderHostObject>(this);\n"
    "    if host.track_view == nil { return; }\n"
    "    let (track, fill, thumb, min, max, value) = (host.track_view, host.fill_view, host.thumb_view, host.minimum_value, host.maximum_value, host.value);\n"
    "    let bounds: CGRect = msg![env; this bounds];\n"
    "    let thumb_w = 20.0f32; let track_h = 4.0f32;\n"
    "    let usable = (bounds.size.width - thumb_w).max(1.0);\n"
    "    let t = if max > min { ((value - min) / (max - min)).clamp(0.0, 1.0) } else { 0.0 };\n"
    "    let cy = bounds.origin.y + bounds.size.height / 2.0;\n"
    "    let track_rect = CGRect { origin: CGPoint { x: bounds.origin.x + thumb_w/2.0, y: cy-track_h/2.0 }, size: CGSize { width: usable, height: track_h } };\n"
    "    let fill_rect = CGRect { origin: track_rect.origin, size: CGSize { width: usable*t, height: track_h } };\n"
    "    let thumb_rect = CGRect { origin: CGPoint { x: bounds.origin.x + usable*t, y: cy-thumb_w/2.0 }, size: CGSize { width: thumb_w, height: thumb_w } };\n"
    "    () = msg![env; track setFrame:track_rect]; () = msg![env; fill setFrame:fill_rect]; () = msg![env; thumb setFrame:thumb_rect];\n"
    "    let layer: id = msg![env; thumb layer]; () = msg![env; layer setCornerRadius:(thumb_w/2.0)];\n"
    "}\n"
    "- (bool)beginTrackingWithTouch:(id)touch withEvent:(id)_event {\n"
    "    let p: CGPoint = msg![env; touch locationInView:this];\n"
    "    let b: CGRect = msg![env; this bounds];\n"
    "    let (min,max) = { let h=env.objc.borrow::<UISliderHostObject>(this); (h.minimum_value,h.maximum_value) };\n"
    "    let t=((p.x-b.origin.x)/b.size.width.max(1.0)).clamp(0.0,1.0); () = msg![env; this setValue:(min+(max-min)*t)];\n"
    "    if msg![env; this isContinuous] { send_actions(env,this,nil,UIControlEventValueChanged); }\n"
    "    true\n"
    "}\n"
    "- (bool)continueTrackingWithTouch:(id)touch withEvent:(id)_event {\n"
    "    let p: CGPoint = msg![env; touch locationInView:this]; let b: CGRect = msg![env; this bounds];\n"
    "    let (min,max) = { let h=env.objc.borrow::<UISliderHostObject>(this); (h.minimum_value,h.maximum_value) };\n"
    "    let t=((p.x-b.origin.x)/b.size.width.max(1.0)).clamp(0.0,1.0); () = msg![env; this setValue:(min+(max-min)*t)];\n"
    "    if msg![env; this isContinuous] { send_actions(env,this,nil,UIControlEventValueChanged); }\n"
    "    true\n"
    "}\n"
    "- (())endTrackingWithTouch:(id)touch withEvent:(id)event {\n"
    "    () = msg_super![env; this endTrackingWithTouch:touch withEvent:event];\n"
    "    if !msg![env; this isContinuous] { send_actions(env,this,event,UIControlEventValueChanged); }\n"
    "}\n\n"
    "- (())setMinimumValueImage:(id)image {",
)

# UIScrollView: persist flags and deliver the drag lifecycle callbacks used by
# UISettingView. We still use immediate scrolling/deceleration for determinism.
replace_once(
    "src/frameworks/uikit/ui_view/ui_scroll_view.rs",
    "    content_size: CGSize,\n}",
    "    content_size: CGSize,\n"
    "    bounces: bool,\n"
    "    paging_enabled: bool,\n"
    "    shows_horizontal_indicator: bool,\n"
    "    shows_vertical_indicator: bool,\n"
    "}",
)
replace_once(
    "src/frameworks/uikit/ui_view/ui_scroll_view.rs",
    "            content_size: CGSize {\n                width: 0.0,\n                height: 0.0,\n            },\n        }",
    "            content_size: CGSize { width: 0.0, height: 0.0 },\n"
    "            bounces: true,\n"
    "            paging_enabled: false,\n"
    "            shows_horizontal_indicator: true,\n"
    "            shows_vertical_indicator: true,\n"
    "        }",
)
replace_once(
    "src/frameworks/uikit/ui_view/ui_scroll_view.rs",
    "- (())setBounces:(id)_bounces {\n    // TODO\n}",
    "- (())setBounces:(bool)bounces { env.objc.borrow_mut::<UIScrollViewHostObject>(this).bounces = bounces; }\n"
    "- (bool)bounces { env.objc.borrow::<UIScrollViewHostObject>(this).bounces }",
)
replace_once(
    "src/frameworks/uikit/ui_view/ui_scroll_view.rs",
    "- (())setPagingEnabled:(bool)enabled {\n    todo_objc_setter!(this, enabled);\n}\n\n- (())setShowsHorizontalScrollIndicator:(bool)value {\n    todo_objc_setter!(this, value);\n}\n\n- (())setShowsVerticalScrollIndicator:(bool)value {\n    todo_objc_setter!(this, value);\n}",
    "- (())setPagingEnabled:(bool)enabled { env.objc.borrow_mut::<UIScrollViewHostObject>(this).paging_enabled = enabled; }\n"
    "- (bool)isPagingEnabled { env.objc.borrow::<UIScrollViewHostObject>(this).paging_enabled }\n\n"
    "- (())setShowsHorizontalScrollIndicator:(bool)value { env.objc.borrow_mut::<UIScrollViewHostObject>(this).shows_horizontal_indicator = value; }\n"
    "- (bool)showsHorizontalScrollIndicator { env.objc.borrow::<UIScrollViewHostObject>(this).shows_horizontal_indicator }\n\n"
    "- (())setShowsVerticalScrollIndicator:(bool)value { env.objc.borrow_mut::<UIScrollViewHostObject>(this).shows_vertical_indicator = value; }\n"
    "- (bool)showsVerticalScrollIndicator { env.objc.borrow::<UIScrollViewHostObject>(this).shows_vertical_indicator }",
)
replace_once(
    "src/frameworks/uikit/ui_view/ui_scroll_view.rs",
    "- (())touchesMoved:(id)touches // NSSet* of UITouch*",
    "- (())touchesBegan:(id)_touches withEvent:(id)_event {\n"
    "    let delegate: id = msg![env; this delegate];\n"
    "    let sel: SEL = env.objc.register_host_selector(\"scrollViewWillBeginDragging:\".to_string(), &mut env.mem);\n"
    "    if delegate != nil && msg![env; delegate respondsToSelector:sel] { () = msg![env; delegate scrollViewWillBeginDragging:this]; }\n"
    "}\n\n"
    "- (())touchesMoved:(id)touches // NSSet* of UITouch*",
)
replace_once(
    "src/frameworks/uikit/ui_view/ui_scroll_view.rs",
    "    }\n}\n\n@end",
    "    }\n"
    "}\n\n"
    "- (())touchesEnded:(id)_touches withEvent:(id)_event {\n"
    "    let delegate: id = msg![env; this delegate];\n"
    "    let sel: SEL = env.objc.register_host_selector(\"scrollViewDidEndDragging:willDecelerate:\".to_string(), &mut env.mem);\n"
    "    if delegate != nil && msg![env; delegate respondsToSelector:sel] { () = msg![env; delegate scrollViewDidEndDragging:this willDecelerate:false]; }\n"
    "}\n\n"
    "@end",
)

# UITextField: decode visible NIB text/font and fire EditingDidEndOnExit so the
# archived EnterFileName action works when Return is pressed.
replace_once(
    "src/frameworks/uikit/ui_view/ui_control/ui_text_field.rs",
    "    // TODO: actual decoding of properties\n\n    let text_label: id = msg_class![env; UILabel new];",
    "    let text_label: id = msg_class![env; UILabel new];",
)
replace_once(
    "src/frameworks/uikit/ui_view/ui_control/ui_text_field.rs",
    "    () = msg![env; this addSubview:text_label];\n\n    this\n}",
    "    () = msg![env; this addSubview:text_label];\n"
    "    let key = ns_string::get_static_str(env, \"UIText\"); let text: id = msg![env; coder decodeObjectForKey:key]; if text != nil { () = msg![env; this setText:text]; }\n"
    "    let key = ns_string::get_static_str(env, \"UITextColor\"); let color: id = msg![env; coder decodeObjectForKey:key]; if color != nil { () = msg![env; this setTextColor:color]; }\n"
    "    let key = ns_string::get_static_str(env, \"UIFont\"); let font: id = msg![env; coder decodeObjectForKey:key]; if font != nil { () = msg![env; this setFont:font]; }\n"
    "    this\n"
    "}",
)
replace_once(
    "src/frameworks/uikit/ui_view/ui_control/ui_text_field.rs",
    "    if msg![env; delegate respondsToSelector:sel] {\n        log_dbg!(\"handle_return\");\n        () = msg![env; delegate textFieldShouldReturn:text_field];\n    }\n}",
    "    let should_return: bool = delegate == nil || !msg![env; delegate respondsToSelector:sel] || msg![env; delegate textFieldShouldReturn:text_field];\n"
    "    if should_return {\n"
    "        () = msg![env; text_field sendActionsForControlEvents:(1u32 << 19)];\n"
    "        let _: bool = msg![env; text_field resignFirstResponder];\n"
    "    }\n"
    "}",
)

# UIRuntimeEventConnection: legacy UIBarButtonItem archives omit UIEventMask;
# UIKit treats activation as the normal touch-up-inside action.
replace_once(
    "src/frameworks/uikit/ui_nib.rs",
    "    let event_mask: i32 = msg![env; coder decodeIntForKey: event_mask_key];\n\n    let host_obj",
    "    let mut event_mask: i32 = msg![env; coder decodeIntForKey: event_mask_key];\n"
    "    if event_mask == 0 { event_mask = 64; }\n\n"
    "    let host_obj",
)

# Replace v8 startup-only bar shims with small, actually interactive legacy
# controls. UITabBarItem/UIBarButtonItem intentionally reuse UIButton.
p = ROOT / "src/frameworks/uikit/ui_nib.rs"
s = p.read_text()
start = s.index("// Minimal legacy bar classes used by Otamatone")
end = s.index("};\n\n/// Takes a [GuestPathBuf] where a nib file is located and deserializes it.", start)
legacy = r'''// Functional legacy bar classes used by iPhone OS 3-era NIBs.
@implementation UINavigationBar: UIView
- (id)initWithCoder:(id)coder {
    let this: id = msg_super![env; this initWithCoder:coder];
    let key = get_static_str(env, "UIItems"); let items: id = msg![env; coder decodeObjectForKey:key];
    let count: NSUInteger = msg![env; items count];
    for i in 0..count { let item: id = msg![env; items objectAtIndex:i]; () = msg![env; this addSubview:item]; }
    this
}
- (())layoutSubviews {
    let bounds: crate::frameworks::core_graphics::CGRect = msg![env; this bounds];
    let subs: id = msg![env; this subviews]; let count: NSUInteger = msg![env; subs count];
    for i in 0..count { let item: id = msg![env; subs objectAtIndex:i]; () = msg![env; item setFrame:bounds]; }
}
@end

@implementation UINavigationItem: UIView
- (id)initWithCoder:(id)coder {
    let zero = crate::frameworks::core_graphics::CGRect::default();
    let this: id = msg_super![env; this initWithFrame:zero];
    let key = get_static_str(env, "UIRightBarButtonItem"); let right: id = msg![env; coder decodeObjectForKey:key];
    if right != nil { () = msg![env; this addSubview:right]; }
    this
}
- (())layoutSubviews {
    let bounds: crate::frameworks::core_graphics::CGRect = msg![env; this bounds];
    let subs: id = msg![env; this subviews]; let count: NSUInteger = msg![env; subs count];
    if count != 0 {
        let button: id = msg![env; subs objectAtIndex:0u32];
        let w = 72.0f32.min(bounds.size.width);
        let frame = crate::frameworks::core_graphics::CGRect { origin: crate::frameworks::core_graphics::CGPoint { x: bounds.origin.x + bounds.size.width - w - 6.0, y: bounds.origin.y + 5.0 }, size: crate::frameworks::core_graphics::CGSize { width: w, height: (bounds.size.height - 10.0).max(0.0) } };
        () = msg![env; button setFrame:frame];
    }
}
@end

@implementation UIBarButtonItem: UIButton
- (id)initWithCoder:(id)coder {
    let zero = crate::frameworks::core_graphics::CGRect::default();
    let this: id = msg_super![env; this initWithFrame:zero];
    let key = get_static_str(env, "UITitle"); let title: id = msg![env; coder decodeObjectForKey:key];
    if title != nil { () = msg![env; this setTitle:title forState:0u32]; }
    let key = get_static_str(env, "UIEnabled"); if msg![env; coder containsValueForKey:key] { let enabled: bool = msg![env; coder decodeBoolForKey:key]; () = msg![env; this setEnabled:enabled]; }
    this
}
@end

@implementation UITabBar: UIView
- (id)initWithCoder:(id)coder {
    let this: id = msg_super![env; this initWithCoder:coder];
    let key = get_static_str(env, "UIItems"); let items: id = msg![env; coder decodeObjectForKey:key];
    let count: NSUInteger = msg![env; items count];
    let sel = env.objc.lookup_selector("_touchHLE_itemSelected:").unwrap();
    for i in 0..count {
        let item: id = msg![env; items objectAtIndex:i]; () = msg![env; item setTag:(i as i32)];
        () = msg![env; item addTarget:this action:sel forControlEvents:64u32]; () = msg![env; this addSubview:item];
    }
    this
}
- (())setDelegate:(id)delegate { crate::frameworks::uikit::ui_view::set_view_controller(env, this, delegate); }
- (id)delegate { msg![env; this nextResponder] }
- (())setSelectedItem:(id)item {
    let subs: id = msg![env; this subviews]; let count: NSUInteger = msg![env; subs count];
    for i in 0..count { let candidate: id = msg![env; subs objectAtIndex:i]; () = msg![env; candidate setSelected:(candidate == item)]; }
}
- (())_touchHLE_itemSelected:(id)item {
    () = msg![env; this setSelectedItem:item];
    let delegate: id = msg![env; this delegate];
    let sel = env.objc.register_host_selector("tabBar:didSelectItem:".to_string(), &mut env.mem);
    if delegate != nil && msg![env; delegate respondsToSelector:sel] { () = msg![env; delegate tabBar:this didSelectItem:item]; }
}
- (())layoutSubviews {
    let bounds: crate::frameworks::core_graphics::CGRect = msg![env; this bounds];
    let subs: id = msg![env; this subviews]; let count: NSUInteger = msg![env; subs count]; if count == 0 { return; }
    let w = bounds.size.width / count as f32;
    for i in 0..count { let item: id = msg![env; subs objectAtIndex:i]; let frame = crate::frameworks::core_graphics::CGRect { origin: crate::frameworks::core_graphics::CGPoint { x: bounds.origin.x + w*i as f32, y: bounds.origin.y }, size: crate::frameworks::core_graphics::CGSize { width: w, height: bounds.size.height } }; () = msg![env; item setFrame:frame]; }
}
@end

@implementation UITabBarItem: UIButton
- (id)initWithCoder:(id)coder {
    let zero = crate::frameworks::core_graphics::CGRect::default();
    let this: id = msg_super![env; this initWithFrame:zero];
    let key = get_static_str(env, "UITitle"); let title: id = msg![env; coder decodeObjectForKey:key]; if title != nil { () = msg![env; this setTitle:title forState:0u32]; }
    let key = get_static_str(env, "UIImage"); let image: id = msg![env; coder decodeObjectForKey:key]; if image != nil { () = msg![env; this setImage:image forState:0u32]; }
    let key = get_static_str(env, "UIEnabled"); if msg![env; coder containsValueForKey:key] { let enabled: bool = msg![env; coder decodeBoolForKey:key]; () = msg![env; this setEnabled:enabled]; }
    this
}
@end

'''
s = s[:start] + legacy + s[end:]
p.write_text(s)

# ---------------------------------------------------------------------------
# UIWebView: retain delegate/request and provide a useful local-HTML fallback.
# It renders readable text (not CSS) and drives the app's delegate callbacks.
# ---------------------------------------------------------------------------
webview = r'''/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */
//! `UIWebView` legacy compatibility.

use crate::frameworks::core_graphics::CGRect;
use crate::frameworks::foundation::{ns_data, ns_string, NSUInteger};
use crate::objc::{id, impl_HostObject_with_superclass, msg, msg_class, msg_super, nil, objc_classes, release, retain, ClassExports, NSZonePtr, SEL};

pub struct UIWebViewHostObject {
    superclass: super::UIViewHostObject,
    delegate: id, // weak
    request: id,
    scales_page_to_fit: bool,
    content_label: id,
}
impl_HostObject_with_superclass!(UIWebViewHostObject);
impl Default for UIWebViewHostObject {
    fn default() -> Self { Self { superclass: Default::default(), delegate: nil, request: nil, scales_page_to_fit: false, content_label: nil } }
}

fn html_to_text(input: &str) -> String {
    let mut out = String::new(); let mut tag = String::new(); let mut in_tag = false;
    for ch in input.chars() {
        if ch == '<' { in_tag = true; tag.clear(); continue; }
        if ch == '>' && in_tag {
            let t = tag.trim().to_ascii_lowercase();
            if t.starts_with("br") || t.starts_with("/p") || t.starts_with("/div") || t.starts_with("/li") || t.starts_with("/h") { out.push('\n'); }
            in_tag = false; continue;
        }
        if in_tag { tag.push(ch); } else { out.push(ch); }
    }
    let out = out.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", "\"");
    let mut clean = String::new(); let mut spaces = 0usize;
    for line in out.lines() {
        let line = line.split_whitespace().collect::<Vec<_>>().join(" ");
        if line.is_empty() { spaces += 1; if spaces > 1 { continue; } } else { spaces = 0; }
        clean.push_str(&line); clean.push('\n');
    }
    clean
}

fn setup_label(env: &mut crate::Environment, this: id) {
    if env.objc.borrow::<UIWebViewHostObject>(this).content_label != nil { return; }
    let label: id = msg_class![env; UILabel new]; () = msg![env; label setNumberOfLines:0i32];
    let white: id = msg_class![env; UIColor whiteColor]; let black: id = msg_class![env; UIColor blackColor];
    () = msg![env; label setBackgroundColor:white]; () = msg![env; label setTextColor:black]; () = msg![env; label setUserInteractionEnabled:false];
    env.objc.borrow_mut::<UIWebViewHostObject>(this).content_label = label; () = msg![env; this addSubview:label];
}

pub const CLASSES: ClassExports = objc_classes! {
(env, this, _cmd);
@implementation UIWebView: UIView
+ (id)allocWithZone:(NSZonePtr)_zone { env.objc.alloc_object(this, Box::<UIWebViewHostObject>::default(), &mut env.mem) }
- (id)initWithFrame:(CGRect)frame { let this: id = msg_super![env; this initWithFrame:frame]; setup_label(env,this); this }
- (id)initWithCoder:(id)coder { let this: id = msg_super![env; this initWithCoder:coder]; setup_label(env,this); this }
- (())dealloc { let h=env.objc.borrow::<UIWebViewHostObject>(this); release(env,h.request); release(env,h.content_label); msg_super![env; this dealloc] }
- (())setScalesPageToFit:(bool)scales { env.objc.borrow_mut::<UIWebViewHostObject>(this).scales_page_to_fit=scales; }
- (bool)scalesPageToFit { env.objc.borrow::<UIWebViewHostObject>(this).scales_page_to_fit }
- (())setDelegate:(id)delegate { env.objc.borrow_mut::<UIWebViewHostObject>(this).delegate=delegate; }
- (id)delegate { env.objc.borrow::<UIWebViewHostObject>(this).delegate }
- (())layoutSubviews { let label=env.objc.borrow::<UIWebViewHostObject>(this).content_label; if label!=nil { let b:CGRect=msg![env; this bounds]; ()=msg![env; label setFrame:b]; } }
- (())loadRequest:(id)request {
    let delegate=env.objc.borrow::<UIWebViewHostObject>(this).delegate;
    if delegate!=nil { let sel:SEL=env.objc.register_host_selector("webView:shouldStartLoadWithRequest:navigationType:".to_string(),&mut env.mem); if msg![env; delegate respondsToSelector:sel] && !msg![env; delegate webView:this shouldStartLoadWithRequest:request navigationType:0i32] { return; } }
    retain(env,request); let old=std::mem::replace(&mut env.objc.borrow_mut::<UIWebViewHostObject>(this).request,request); release(env,old);
    if request!=nil { let url:id=msg![env; request URL]; let data:id=msg_class![env; NSData dataWithContentsOfURL:url]; if data!=nil { let len:NSUInteger=msg![env; data length]; if len!=0 { let bytes=ns_data::to_rust_slice(env,data); let html=String::from_utf8_lossy(bytes); let plain=html_to_text(&html); let text=ns_string::from_rust_string(env,plain); let label=env.objc.borrow::<UIWebViewHostObject>(this).content_label; ()=msg![env; label setText:text]; } } }
    if delegate!=nil { let sel:SEL=env.objc.register_host_selector("webViewDidFinishLoad:".to_string(),&mut env.mem); if msg![env; delegate respondsToSelector:sel] { ()=msg![env; delegate webViewDidFinishLoad:this]; } }
}
@end
};
'''
(ROOT / "src/frameworks/uikit/ui_view/ui_web_view.rs").write_text(webview)

print("Applied Otamatone v11 comprehensive legacy UIKit compatibility patch")
