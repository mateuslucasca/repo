#import "GameProjectAppDelegate.h"
#import "EAGLView.h"
#import "MainMode.h"
#import "OtamatoneCore.h"
@implementation GameProjectAppDelegate
-(BOOL)application:(UIApplication*)app didFinishLaunchingWithOptions:(NSDictionary*)opts{app.idleTimerDisabled=YES;self.window=[[UIWindow alloc]initWithFrame:UIScreen.mainScreen.bounds];UIViewController*vc=[UIViewController new];vc.view.backgroundColor=UIColor.blackColor;self.glView=[[EAGLView alloc]initWithFrame:vc.view.bounds];self.glView.autoresizingMask=UIViewAutoresizingFlexibleWidth|UIViewAutoresizingFlexibleHeight;[vc.view addSubview:self.glView];self.window.rootViewController=vc;[self.window makeKeyAndVisible];[self.glView startAnimation];return YES;}
-(void)applicationDidFinishLaunching:(UIApplication*)app{if(!self.window)[self application:app didFinishLaunchingWithOptions:nil];}
-(void)applicationDidBecomeActive:(UIApplication*)app{[self.glView startAnimation];}-(void)applicationWillResignActive:(UIApplication*)app{[self.glView stopAnimation];[self.glView.mainMode.audio setPitch:self.glView.mainMode.pitch mouth:self.glView.mainMode.mouth active:NO];}-(void)applicationWillTerminate:(UIApplication*)app{[self.glView.mainMode SaveParam];[self.glView.mainMode Quit];}
-(void)ResetAccelerometer{ACRReset();}-(void)accelerometer:(id)a didAccelerate:(id)x{if([x respondsToSelector:@selector(x)])ACRSetAcc([[x valueForKey:@"x"]floatValue],[[x valueForKey:@"y"]floatValue],[[x valueForKey:@"z"]floatValue]);}
-(UIInterfaceOrientationMask)application:(UIApplication*)a supportedInterfaceOrientationsForWindow:(UIWindow*)w{return UIInterfaceOrientationMaskPortrait;}
@end
