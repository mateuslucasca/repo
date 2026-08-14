from pathlib import Path
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "touchhle")


def replace_once(rel, old, new):
    p = ROOT / rel
    s = p.read_text()
    count = s.count(old)
    if count != 1:
        raise RuntimeError(f"Expected one match in {rel}: {old!r}; found {count}")
    p.write_text(s.replace(old, new, 1))


ns_calendar = r'''/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */
//! Minimal NSCalendar/NSDateComponents support for legacy iPhone OS apps.

use super::{ns_string, NSInteger, NSTimeInterval, NSUInteger};
use crate::dyld::{ConstantExports, HostConstant};
use crate::frameworks::core_foundation::time::CFAbsoluteTimeGetGregorianDate;
use crate::objc::{autorelease, id, msg, nil, objc_classes, ClassExports, HostObject, NSZonePtr};

const NS_GREGORIAN_CALENDAR: &str = "gregorian";
type NSCalendarUnit = NSUInteger;

#[derive(Default)]
struct NSCalendarHostObject;
impl HostObject for NSCalendarHostObject {}

#[derive(Default)]
struct NSDateComponentsHostObject {
    year: NSInteger,
    month: NSInteger,
    day: NSInteger,
    hour: NSInteger,
    minute: NSInteger,
    second: NSInteger,
}
impl HostObject for NSDateComponentsHostObject {}

pub const CLASSES: ClassExports = objc_classes! {

(env, this, _cmd);

@implementation NSCalendar: NSObject

+ (id)allocWithZone:(NSZonePtr)_zone {
    env.objc.alloc_object(this, Box::<NSCalendarHostObject>::default(), &mut env.mem)
}

- (id)initWithCalendarIdentifier:(id)identifier {
    let identifier = ns_string::to_rust_string(env, identifier);
    log!("Otamatone trace: NSCalendar initWithCalendarIdentifier={:?}", identifier);
    if identifier != NS_GREGORIAN_CALENDAR {
        log!("Warning: NSCalendar identifier {:?} is not fully supported; treating it as Gregorian", identifier);
    }
    this
}

- (id)components:(NSCalendarUnit)unit_flags fromDate:(id)date {
    let time_interval: NSTimeInterval = msg![env; date timeIntervalSinceReferenceDate];
    let gregorian = CFAbsoluteTimeGetGregorianDate(env, time_interval, nil);
    // CFGregorianDate is #[repr(C, packed)]. Copy fields before passing them to
    // formatting macros, which would otherwise create unaligned references.
    let year = gregorian.year;
    let month: NSInteger = gregorian.month.into();
    let day: NSInteger = gregorian.day.into();
    let hour: NSInteger = gregorian.hours.into();
    let minute: NSInteger = gregorian.minutes.into();
    let second = gregorian.seconds as NSInteger;
    log!(
        "Otamatone trace: NSCalendar components flags={:#x} => {:04}-{:02}-{:02} {:02}:{:02}:{:02}",
        unit_flags,
        year,
        month,
        day,
        hour,
        minute,
        second,
    );
    let class = env.objc.get_known_class("NSDateComponents", &mut env.mem);
    let components = env.objc.alloc_object(
        class,
        Box::new(NSDateComponentsHostObject {
            year,
            month,
            day,
            hour,
            minute,
            second,
        }),
        &mut env.mem,
    );
    autorelease(env, components)
}

@end

@implementation NSDateComponents: NSObject

+ (id)allocWithZone:(NSZonePtr)_zone {
    env.objc.alloc_object(this, Box::<NSDateComponentsHostObject>::default(), &mut env.mem)
}

- (NSInteger)year { env.objc.borrow::<NSDateComponentsHostObject>(this).year }
- (NSInteger)month { env.objc.borrow::<NSDateComponentsHostObject>(this).month }
- (NSInteger)day { env.objc.borrow::<NSDateComponentsHostObject>(this).day }
- (NSInteger)hour { env.objc.borrow::<NSDateComponentsHostObject>(this).hour }
- (NSInteger)minute { env.objc.borrow::<NSDateComponentsHostObject>(this).minute }
- (NSInteger)second { env.objc.borrow::<NSDateComponentsHostObject>(this).second }

@end

};

pub const CONSTANTS: ConstantExports = &[
    ("_NSGregorianCalendar", HostConstant::NSString(NS_GREGORIAN_CALENDAR)),
];
'''
(ROOT / "src/frameworks/foundation/ns_calendar.rs").write_text(ns_calendar)

replace_once(
    "src/frameworks/foundation.rs",
    "pub mod ns_bundle;\n",
    "pub mod ns_bundle;\npub mod ns_calendar;\n",
)
replace_once(
    "src/frameworks/foundation.rs",
    "        ns_bundle::CLASSES,\n",
    "        ns_bundle::CLASSES,\n        ns_calendar::CLASSES,\n",
)
replace_once(
    "src/frameworks/foundation.rs",
    "    constant_exports: &[\n        ns_error::CONSTANTS,\n",
    "    constant_exports: &[\n        ns_calendar::CONSTANTS,\n        ns_error::CONSTANTS,\n",
)

p = ROOT / "src/frameworks/uikit/ui_view/ui_scroll_view.rs"
s = p.read_text()
s = s.replace(
    "use crate::frameworks::core_graphics::{CGPoint, CGRect, CGSize};",
    "use crate::dyld::{ConstantExports, HostConstant};\nuse crate::frameworks::core_graphics::{CGFloat, CGPoint, CGRect, CGSize};",
    1,
)
s = s.replace(
    "type UIScrollViewIndicatorStyle = NSInteger;\n",
    "type UIScrollViewIndicatorStyle = NSInteger;\ntype UIScrollViewDecelerationRate = CGFloat;\n\nconst DECELERATION_RATE_NORMAL: UIScrollViewDecelerationRate = 0.998;\nconst DECELERATION_RATE_FAST: UIScrollViewDecelerationRate = 0.99;\n",
    1,
)
s = s.replace(
    "    scroll_enabled: bool,\n    content_offset: CGPoint,",
    "    scroll_enabled: bool,\n    deceleration_rate: UIScrollViewDecelerationRate,\n    content_offset: CGPoint,",
    1,
)
s = s.replace(
    "            scroll_enabled: true,\n            content_offset:",
    "            scroll_enabled: true,\n            deceleration_rate: DECELERATION_RATE_NORMAL,\n            content_offset:",
    1,
)
marker = "- (())setScrollEnabled:(bool)scroll_enabled {\n    env.objc.borrow_mut::<UIScrollViewHostObject>(this).scroll_enabled = scroll_enabled;\n}\n"
if s.count(marker) != 1:
    raise RuntimeError("Could not locate setScrollEnabled")
s = s.replace(
    marker,
    marker
    + "\n- (UIScrollViewDecelerationRate)decelerationRate {\n"
      "    env.objc.borrow::<UIScrollViewHostObject>(this).deceleration_rate\n"
      "}\n"
      "- (())setDecelerationRate:(UIScrollViewDecelerationRate)rate {\n"
      "    log!(\"Otamatone trace: UIScrollView setDecelerationRate {}\", rate);\n"
      "    env.objc.borrow_mut::<UIScrollViewHostObject>(this).deceleration_rate = rate;\n"
      "}\n",
    1,
)
marker = "- (())setContentOffset:(CGPoint)offset {\n    env.objc.borrow_mut::<UIScrollViewHostObject>(this).content_offset = offset;\n    // Bounds origin should be equals to the content offset\n    let mut bounds: CGRect = msg![env; this bounds];\n    bounds.origin = offset;\n    () = msg![env; this setBounds:bounds];\n    () = msg![env; this setNeedsDisplay];\n}\n"
if s.count(marker) != 1:
    raise RuntimeError("Could not locate setContentOffset")
s = s.replace(
    marker,
    marker
    + "\n- (())setContentOffset:(CGPoint)offset animated:(bool)animated {\n"
      "    log!(\"Otamatone trace: UIScrollView setContentOffset {:?} animated={}\", offset, animated);\n"
      "    () = msg![env; this setContentOffset:offset];\n"
      "    if animated {\n"
      "        let delegate: id = msg![env; this delegate];\n"
      "        let sel: SEL = env.objc.register_host_selector(\"scrollViewDidEndScrollingAnimation:\".to_string(), &mut env.mem);\n"
      "        let responds: bool = msg![env; delegate respondsToSelector:sel];\n"
      "        if responds {\n"
      "            () = msg![env; delegate scrollViewDidEndScrollingAnimation:this];\n"
      "        }\n"
      "    }\n"
      "}\n",
    1,
)
s += r'''

pub const CONSTANTS: ConstantExports = &[
    (
        "_UIScrollViewDecelerationRateNormal",
        HostConstant::Custom(|env| env.mem.alloc_and_write(DECELERATION_RATE_NORMAL).cast().cast_const()),
    ),
    (
        "_UIScrollViewDecelerationRateFast",
        HostConstant::Custom(|env| env.mem.alloc_and_write(DECELERATION_RATE_FAST).cast().cast_const()),
    ),
];
'''
p.write_text(s)

replace_once(
    "src/frameworks/uikit.rs",
    "        ui_device::CONSTANTS,\n",
    "        ui_device::CONSTANTS,\n        ui_view::ui_scroll_view::CONSTANTS,\n",
)

# The touchHLE debugging guide specifically recommends ABI + dyld tracing when
# a guest dies without a useful panic. This is intentionally noisy for v2.
replace_once(
    "src/log.rs",
    'pub const ENABLED_MODULES: &[&str] = &[];',
    'pub const ENABLED_MODULES: &[&str] = &["touchHLE::abi", "touchHLE::dyld"];',
)

print("Applied Otamatone v2 compatibility + ABI/dyld diagnostic patch")
