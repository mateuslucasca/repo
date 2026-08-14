#import <UIKit/UIKit.h>
@class EAGLView;
@interface GameProjectAppDelegate:UIResponder<UIApplicationDelegate>@property(nonatomic,strong)UIWindow*window;@property(nonatomic,strong)EAGLView*glView;-(void)ResetAccelerometer;@end
