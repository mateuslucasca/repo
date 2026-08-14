#import <UIKit/UIKit.h>
@class MainMode;
@interface EAGLView:UIView
@property(nonatomic,strong,readonly)MainMode*mainMode;@property(nonatomic)NSTimeInterval animationInterval;
-(void)Initialize;-(void)InitGUI;-(MainMode*)GetMainMode;-(void)startAnimation;-(void)stopAnimation;-(void)drawView;-(void)OpenMenu;-(void)CloseMenu;-(void)CloseMenuEnd;-(void)OpenMusicList;-(void)OpenMusicList2;-(void)CloseMusicListToMenu;-(void)CloseMusicListToMelody;-(void)CloseMenuToPlayList;-(void)OpenHowTo;-(void)OpenAbout;-(void)OpenNameEntry;-(void)OpenAlert:(NSInteger)type;-(void)InitAlert;-(void)InitSettingView;-(void)StopMusic;-(void)SetMusicIndex01;-(void)SetMusicIndex02;-(void)SetMusicIndex03;-(void)SetMusicIndex04;-(void)SetMusicIndex05;-(void)SetMusicIndex06;-(void)SetMusicIndex07;-(void)SetMusicIndex08;-(void)SetMusicIndex09;-(void)SetMusicIndex10;-(void)SetMusicIndex11;
@end
