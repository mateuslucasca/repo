from pathlib import Path
import subprocess
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "touchhle")
HELPER = Path(__file__).with_name("apply_touchhle_otamatone_v11_fixed.py")
subprocess.run([sys.executable, str(HELPER), str(ROOT)], check=True)


def replace_once(rel, old, new):
    p = ROOT / rel
    s = p.read_text()
    count = s.count(old)
    if count != 1:
        raise RuntimeError(f"Expected one match in {rel}: {old!r}; found {count}")
    p.write_text(s.replace(old, new, 1))


# ---------------------------------------------------------------------------
# NSValue + Core Animation: make CGAffineTransform a first-class animatable
# value. This removes the v10 TODO where old iOS UIView animations jumped
# directly to their final translated positions.
# ---------------------------------------------------------------------------
replace_once(
    "src/frameworks/foundation/ns_value.rs",
    "use crate::frameworks::core_graphics::{CGPoint, CGRect, CGSize};",
    "use crate::frameworks::core_graphics::{CGAffineTransform, CGPoint, CGRect, CGSize};",
)
replace_once(
    "src/frameworks/foundation/ns_value.rs",
    "    CGRect(CGRect),\n}",
    "    CGRect(CGRect),\n    CGAffineTransform(CGAffineTransform),\n}",
)
replace_once(
    "src/frameworks/foundation/ns_value.rs",
    "+ (id)valueWithCGRect:(CGRect)value {\n    let host_object = Box::new(NSValueHostObject::CGRect(value));\n    let new = env.objc.alloc_object(this, host_object, &mut env.mem);\n    autorelease(env, new)\n}\n",
    "+ (id)valueWithCGRect:(CGRect)value {\n"
    "    let host_object = Box::new(NSValueHostObject::CGRect(value));\n"
    "    let new = env.objc.alloc_object(this, host_object, &mut env.mem);\n"
    "    autorelease(env, new)\n"
    "}\n\n"
    "+ (id)valueWithCGAffineTransform:(CGAffineTransform)value {\n"
    "    let host_object = Box::new(NSValueHostObject::CGAffineTransform(value));\n"
    "    let new = env.objc.alloc_object(this, host_object, &mut env.mem);\n"
    "    autorelease(env, new)\n"
    "}\n",
)
replace_once(
    "src/frameworks/foundation/ns_value.rs",
    "- (CGRect)CGRectValue {\n    let host_object = env.objc.borrow::<NSValueHostObject>(this);\n    match host_object {\n        NSValueHostObject::CGRect(cg_rect) => *cg_rect,\n        _ => unimplemented!()\n    }\n}\n",
    "- (CGRect)CGRectValue {\n"
    "    let host_object = env.objc.borrow::<NSValueHostObject>(this);\n"
    "    match host_object {\n"
    "        NSValueHostObject::CGRect(cg_rect) => *cg_rect,\n"
    "        _ => unimplemented!()\n"
    "    }\n"
    "}\n\n"
    "- (CGAffineTransform)CGAffineTransformValue {\n"
    "    let host_object = env.objc.borrow::<NSValueHostObject>(this);\n"
    "    match host_object {\n"
    "        NSValueHostObject::CGAffineTransform(value) => *value,\n"
    "        _ => unimplemented!()\n"
    "    }\n"
    "}\n",
)

replace_once(
    "src/frameworks/core_animation/ca_layer.rs",
    "    if is_implicit_animation_enabled(env, this) && old_affine_transform != affine_transform {\n        log!(\"TODO: Implicit animation for affineTransform change from {old_affine_transform:?} to {affine_transform:?}\");\n    }",
    "    if is_implicit_animation_enabled(env, this) && old_affine_transform != affine_transform {\n"
    "        let old_value: id = msg_class![env; NSValue valueWithCGAffineTransform:old_affine_transform];\n"
    "        let new_value: id = msg_class![env; NSValue valueWithCGAffineTransform:affine_transform];\n"
    "        add_default_implied_basic_animation(env, this, \"affineTransform\", old_value, new_value);\n"
    "    }",
)

replace_once(
    "src/frameworks/core_animation/animation.rs",
    "use crate::frameworks::core_graphics::cg_color::CGColorHostObject;",
    "use crate::frameworks::core_graphics::cg_color::CGColorHostObject;\nuse crate::frameworks::core_graphics::CGAffineTransform;",
)
replace_once(
    "src/frameworks/core_animation/animation.rs",
    "                \"backgroundColor\" => {",
    "                \"affineTransform\" => {\n"
    "                    let from_value = id_as_option(from_value).map(|obj| msg![env; obj CGAffineTransformValue]);\n"
    "                    let to_value = id_as_option(to_value).map(|obj| msg![env; obj CGAffineTransformValue]);\n"
    "                    let by_value = id_as_option(by_value).map(|obj| msg![env; obj CGAffineTransformValue]);\n"
    "                    let (from_value, by_value) = get_affine_from_and_by_values(\n"
    "                        presentation.affine_transform, from_value, to_value, by_value\n"
    "                    );\n"
    "                    presentation.affine_transform = affine_add_scaled(from_value, by_value, interpolation_amount);\n"
    "                }\n"
    "                \"backgroundColor\" => {",
)
replace_once(
    "src/frameworks/core_animation/animation.rs",
    "fn get_from_and_by_values<T>(",
    "fn affine_sub(lhs: CGAffineTransform, rhs: CGAffineTransform) -> CGAffineTransform {\n"
    "    let CGAffineTransform { a: la, b: lb, c: lc, d: ld, tx: ltx, ty: lty } = lhs;\n"
    "    let CGAffineTransform { a: ra, b: rb, c: rc, d: rd, tx: rtx, ty: rty } = rhs;\n"
    "    CGAffineTransform { a: la-ra, b: lb-rb, c: lc-rc, d: ld-rd, tx: ltx-rtx, ty: lty-rty }\n"
    "}\n\n"
    "fn affine_add_scaled(base: CGAffineTransform, delta: CGAffineTransform, amount: f32) -> CGAffineTransform {\n"
    "    let CGAffineTransform { a, b, c, d, tx, ty } = base;\n"
    "    let CGAffineTransform { a: da, b: db, c: dc, d: dd, tx: dtx, ty: dty } = delta;\n"
    "    CGAffineTransform { a: a+da*amount, b: b+db*amount, c: c+dc*amount, d: d+dd*amount, tx: tx+dtx*amount, ty: ty+dty*amount }\n"
    "}\n\n"
    "fn get_affine_from_and_by_values(\n"
    "    current: CGAffineTransform,\n"
    "    from: Option<CGAffineTransform>,\n"
    "    to: Option<CGAffineTransform>,\n"
    "    by: Option<CGAffineTransform>,\n"
    ") -> (CGAffineTransform, CGAffineTransform) {\n"
    "    match (from, to, by) {\n"
    "        (Some(f), Some(t), None) => (f, affine_sub(t, f)),\n"
    "        (Some(f), None, Some(b)) => (f, b),\n"
    "        (None, Some(t), Some(b)) => (affine_sub(t, b), b),\n"
    "        (Some(f), None, None) => (f, affine_sub(current, f)),\n"
    "        (None, Some(t), None) => (current, affine_sub(t, current)),\n"
    "        (None, None, Some(b)) => (current, b),\n"
    "        (Some(_), Some(_), Some(_)) => panic!(\"Cannot specify all three affine animation values\"),\n"
    "        (None, None, None) => (current, affine_sub(current, current)),\n"
    "    }\n"
    "}\n\n"
    "fn get_from_and_by_values<T>(",
)

# ---------------------------------------------------------------------------
# Real masksToBounds clipping in the compositor. Keep clip rectangles in
# screen-space UIKit points, intersect them through the layer tree, then apply
# OpenGL scissor rectangles when drawing each descendant.
# ---------------------------------------------------------------------------
replace_once(
    "src/frameworks/core_animation/composition.rs",
    "                opacity,\n            );",
    "                opacity,\n                None,\n            );",
)
replace_once(
    "src/frameworks/core_animation/composition.rs",
    "    opacity: CGFloat,\n) {",
    "    opacity: CGFloat,\n    inherited_clip: Option<CGRect>,\n) {",
)
replace_once(
    "src/frameworks/core_animation/composition.rs",
    "    let window = env.window.as_mut().unwrap();\n    let mut gles = window.make_internal_gl_ctx_current();\n\n    let opacity = opacity * host_obj.opacity;",
    "    // Apply the clip inherited from any ancestor with masksToBounds.\n"
    "    let screen_bounds: CGRect = {\n"
    "        let screen: id = msg_class![env; UIScreen mainScreen];\n"
    "        msg![env; screen bounds]\n"
    "    };\n"
    "    let scale = env.options.scale_hack.get() as f32;\n"
    "    let scissor = inherited_clip.map(|r| clip_to_scissor(r, screen_bounds, scale));\n"
    "    let window = env.window.as_mut().unwrap();\n"
    "    let mut gles = window.make_internal_gl_ctx_current();\n"
    "    if let Some((x, y, w, h)) = scissor {\n"
    "        gles.Enable(gles11::SCISSOR_TEST);\n"
    "        gles.Scissor(x, y, w, h);\n"
    "    } else {\n"
    "        gles.Disable(gles11::SCISSOR_TEST);\n"
    "    }\n\n"
    "    let opacity = opacity * host_obj.opacity;",
)
replace_once(
    "src/frameworks/core_animation/composition.rs",
    "    // avoid holding mutable borrow while recursing\n    let original_host_obj = env.objc.borrow_mut::<CALayerHostObject>(layer);\n    for &child_layer in &original_host_obj.sublayers.clone() {\n        // TODO: clipping/masksToBounds support\n        composite_layer_recursive(\n            env,\n            animation_state,\n            child_layer,\n            cumulative_transform,\n            opacity,\n        )\n    }",
    "    let child_clip = if host_obj.masks_to_bounds {\n"
    "        let bounds = host_obj.bounds;\n"
    "        let own_clip: CGRect = msg![env; layer convertRect:bounds toLayer:nil];\n"
    "        Some(match inherited_clip {\n"
    "            Some(parent) => intersect_rect(parent, own_clip),\n"
    "            None => own_clip,\n"
    "        })\n"
    "    } else {\n"
    "        inherited_clip\n"
    "    };\n"
    "    // avoid holding mutable borrow while recursing\n"
    "    let original_host_obj = env.objc.borrow_mut::<CALayerHostObject>(layer);\n"
    "    for &child_layer in &original_host_obj.sublayers.clone() {\n"
    "        composite_layer_recursive(\n"
    "            env, animation_state, child_layer, cumulative_transform, opacity, child_clip\n"
    "        )\n"
    "    }",
)
replace_once(
    "src/frameworks/core_animation/composition.rs",
    "const FLOATS_PER_POINT: usize = 2;",
    "fn intersect_rect(a: CGRect, b: CGRect) -> CGRect {\n"
    "    let x1 = a.origin.x.max(b.origin.x);\n"
    "    let y1 = a.origin.y.max(b.origin.y);\n"
    "    let x2 = (a.origin.x + a.size.width).min(b.origin.x + b.size.width);\n"
    "    let y2 = (a.origin.y + a.size.height).min(b.origin.y + b.size.height);\n"
    "    CGRect {\n"
    "        origin: crate::frameworks::core_graphics::CGPoint { x: x1, y: y1 },\n"
    "        size: crate::frameworks::core_graphics::CGSize { width: (x2-x1).max(0.0), height: (y2-y1).max(0.0) },\n"
    "    }\n"
    "}\n\n"
    "fn clip_to_scissor(rect: CGRect, screen: CGRect, scale: f32) -> (GLint, GLint, GLsizei, GLsizei) {\n"
    "    let clipped = intersect_rect(rect, screen);\n"
    "    let x1 = ((clipped.origin.x - screen.origin.x) * scale).floor().max(0.0);\n"
    "    let x2 = ((clipped.origin.x + clipped.size.width - screen.origin.x) * scale).ceil().max(x1);\n"
    "    let top = ((clipped.origin.y - screen.origin.y) * scale).floor().max(0.0);\n"
    "    let bottom = ((clipped.origin.y + clipped.size.height - screen.origin.y) * scale).ceil().max(top);\n"
    "    let fb_height = (screen.size.height * scale).round();\n"
    "    (x1 as GLint, (fb_height-bottom).max(0.0) as GLint, (x2-x1) as GLsizei, (bottom-top) as GLsizei)\n"
    "}\n\n"
    "const FLOATS_PER_POINT: usize = 2;",
)

print("Applied Otamatone v11 affine animation + compositor clipping pass")
