from pathlib import Path
import subprocess
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "touchhle")
HELPER = Path(__file__).with_name("apply_touchhle_otamatone_v8.py")

# Keep every compatibility fix and the compact keyed-archive diagnostics from v8.
subprocess.run([sys.executable, str(HELPER), str(ROOT)], check=True)

slider = ROOT / "src/frameworks/uikit/ui_view/ui_control/ui_slider.rs"
slider.write_text(r'''/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */
//! `UISlider`.

use crate::environment::Environment;
use crate::frameworks::core_graphics::CGRect;
use crate::objc::{
    id, impl_HostObject_with_superclass, msg, msg_super, nil, objc_classes, release, retain,
    ClassExports, NSZonePtr,
};

pub struct UISliderHostObject {
    superclass: super::UIControlHostObject,
    minimum_value: f32,
    maximum_value: f32,
    value: f32,
    continuous: bool,
    /// Only the normal-state images are currently needed by Otamatone's
    /// UICustomSwitch. Keeping them retained also makes currentThumbImage work.
    thumb_image: id,
    minimum_track_image: id,
    maximum_track_image: id,
    minimum_value_image: id,
    maximum_value_image: id,
}
impl_HostObject_with_superclass!(UISliderHostObject);

impl Default for UISliderHostObject {
    fn default() -> Self {
        Self {
            superclass: Default::default(),
            minimum_value: 0.0,
            maximum_value: 1.0,
            value: 0.0,
            continuous: true,
            thumb_image: nil,
            minimum_track_image: nil,
            maximum_track_image: nil,
            minimum_value_image: nil,
            maximum_value_image: nil,
        }
    }
}

fn clamp_value(host: &mut UISliderHostObject) {
    if host.minimum_value <= host.maximum_value {
        host.value = host.value.clamp(host.minimum_value, host.maximum_value);
    }
}

fn replace_image(env: &mut Environment, slot: &mut id, image: id) {
    retain(env, image);
    let old = std::mem::replace(slot, image);
    release(env, old);
}

pub const CLASSES: ClassExports = objc_classes! {

(env, this, _cmd);

@implementation UISlider: UIControl

+ (id)allocWithZone:(NSZonePtr)_zone {
    let host_object = Box::<UISliderHostObject>::default();
    env.objc.alloc_object(this, host_object, &mut env.mem)
}

- (id)initWithFrame:(CGRect)frame {
    log!("Otamatone v9: UISlider initWithFrame this={:?} frame={:?}", this, frame);
    msg_super![env; this initWithFrame:frame]
}

// NSCoding implementation. The UIView/UIControl superclass decoder handles
// the geometry and common control state. Slider-specific archived values are
// not required for Otamatone's startup; its UICustomSwitch configures them
// immediately from awakeFromNib.
- (id)initWithCoder:(id)coder {
    log!("Otamatone v9: UISlider initWithCoder this={:?} coder={:?}", this, coder);
    msg_super![env; this initWithCoder:coder]
}

- (())dealloc {
    let UISliderHostObject {
        superclass: _,
        minimum_value: _,
        maximum_value: _,
        value: _,
        continuous: _,
        thumb_image,
        minimum_track_image,
        maximum_track_image,
        minimum_value_image,
        maximum_value_image,
    } = std::mem::take(env.objc.borrow_mut(this));
    release(env, thumb_image);
    release(env, minimum_track_image);
    release(env, maximum_track_image);
    release(env, minimum_value_image);
    release(env, maximum_value_image);
    msg_super![env; this dealloc]
}

- (f32)minimumValue {
    env.objc.borrow::<UISliderHostObject>(this).minimum_value
}
- (())setMinimumValue:(f32)value {
    let host = env.objc.borrow_mut::<UISliderHostObject>(this);
    host.minimum_value = value;
    clamp_value(host);
}

- (f32)maximumValue {
    env.objc.borrow::<UISliderHostObject>(this).maximum_value
}
- (())setMaximumValue:(f32)value {
    let host = env.objc.borrow_mut::<UISliderHostObject>(this);
    host.maximum_value = value;
    clamp_value(host);
}

- (f32)value {
    env.objc.borrow::<UISliderHostObject>(this).value
}
- (())setValue:(f32)value {
    let host = env.objc.borrow_mut::<UISliderHostObject>(this);
    host.value = value;
    clamp_value(host);
}
- (())setValue:(f32)value animated:(bool)_animated {
    () = msg![env; this setValue:value];
}

- (bool)isContinuous {
    env.objc.borrow::<UISliderHostObject>(this).continuous
}
- (bool)continuous {
    env.objc.borrow::<UISliderHostObject>(this).continuous
}
- (())setContinuous:(bool)continuous {
    env.objc.borrow_mut::<UISliderHostObject>(this).continuous = continuous;
}

- (())setThumbImage:(id)image forState:(u32)_state {
    log!("Otamatone v9: UISlider setThumbImage this={:?} image={:?}", this, image);
    let old = env.objc.borrow::<UISliderHostObject>(this).thumb_image;
    retain(env, image);
    env.objc.borrow_mut::<UISliderHostObject>(this).thumb_image = image;
    release(env, old);
}
- (id)thumbImageForState:(u32)_state {
    env.objc.borrow::<UISliderHostObject>(this).thumb_image
}
- (id)currentThumbImage {
    env.objc.borrow::<UISliderHostObject>(this).thumb_image
}

- (())setMinimumTrackImage:(id)image forState:(u32)_state {
    let old = env.objc.borrow::<UISliderHostObject>(this).minimum_track_image;
    retain(env, image);
    env.objc.borrow_mut::<UISliderHostObject>(this).minimum_track_image = image;
    release(env, old);
}
- (id)minimumTrackImageForState:(u32)_state {
    env.objc.borrow::<UISliderHostObject>(this).minimum_track_image
}
- (id)currentMinimumTrackImage {
    env.objc.borrow::<UISliderHostObject>(this).minimum_track_image
}

- (())setMaximumTrackImage:(id)image forState:(u32)_state {
    let old = env.objc.borrow::<UISliderHostObject>(this).maximum_track_image;
    retain(env, image);
    env.objc.borrow_mut::<UISliderHostObject>(this).maximum_track_image = image;
    release(env, old);
}
- (id)maximumTrackImageForState:(u32)_state {
    env.objc.borrow::<UISliderHostObject>(this).maximum_track_image
}
- (id)currentMaximumTrackImage {
    env.objc.borrow::<UISliderHostObject>(this).maximum_track_image
}

- (())setMinimumValueImage:(id)image {
    let old = env.objc.borrow::<UISliderHostObject>(this).minimum_value_image;
    retain(env, image);
    env.objc.borrow_mut::<UISliderHostObject>(this).minimum_value_image = image;
    release(env, old);
}
- (id)minimumValueImage {
    env.objc.borrow::<UISliderHostObject>(this).minimum_value_image
}

- (())setMaximumValueImage:(id)image {
    let old = env.objc.borrow::<UISliderHostObject>(this).maximum_value_image;
    retain(env, image);
    env.objc.borrow_mut::<UISliderHostObject>(this).maximum_value_image = image;
    release(env, old);
}
- (id)maximumValueImage {
    env.objc.borrow::<UISliderHostObject>(this).maximum_value_image
}

@end

};
''')

# UICustomSwitch uses this normal UIControl API after a touch ends. Implement it
# now so the switch can remain usable once startup finally completes.
ui_control = ROOT / "src/frameworks/uikit/ui_view/ui_control.rs"
s = ui_control.read_text()
needle = '''- (())sendAction:(SEL)action
              to:(id)target
        forEvent:(id)event { // UIEvent*
'''
insert = '''- (())sendActionsForControlEvents:(UIControlEvents)events {
    send_actions(env, this, nil, events);
}

- (())sendAction:(SEL)action
              to:(id)target
        forEvent:(id)event { // UIEvent*
'''
if s.count(needle) != 1:
    raise RuntimeError(f"Expected one UIControl sendAction insertion point; found {s.count(needle)}")
ui_control.write_text(s.replace(needle, insert, 1))

print("Applied Otamatone v9 UISlider state/image compatibility + UIControl sendActionsForControlEvents")
