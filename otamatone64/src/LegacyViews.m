#import <UIKit/UIKit.h>
#import <WebKit/WebKit.h>
// Keep every custom UIKit class name present in MainWindow.nib so later passes
// can load portions of the original archive without class-substitution hacks.
@interface UICustomSwitch:UISwitch@end @implementation UICustomSwitch@end
@interface UIMenuView:UIView@end @implementation UIMenuView@end
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
