#import <UIKit/UIKit.h>
#import <WebKit/WebKit.h>
// Keep the legacy custom UIKit class names that do not collide with symbols
// introduced by modern UIKit. UIMenuView is intentionally omitted here:
// iOS 13+ exports a UIMenuIdentifier constant with that exact C symbol name.
// The first native port does not unarchive MainWindow.nib, so the class is not
// needed at runtime; if the old NIB path is restored later, create it through
// the Objective-C runtime instead of a compile-time @interface.
@interface UICustomSwitch:UISwitch@end @implementation UICustomSwitch@end
@interface UIMusicList:UIView@end @implementation UIMusicList@end
@interface UISettingView:UIView@end @implementation UISettingView@end
@interface UIMelodyListView:UIView@end @implementation UIMelodyListView@end
@interface UIMelodyListCellView:UIView@end @implementation UIMelodyListCellView@end
@interface UIHtmlView:UIView@end @implementation UIHtmlView@end
@interface UINameEntryView:UIView@end @implementation UINameEntryView@end
@interface AlertView:UIView@end @implementation AlertView@end
@interface SettingView:UIView@end @implementation SettingView@end
@interface UISimpleHtml:WKWebView@end
@implementation UISimpleHtml
-(instancetype)initWithFrame:(CGRect)f{ return [super initWithFrame:f configuration:[WKWebViewConfiguration new]]; }
@end
