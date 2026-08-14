#import <Foundation/Foundation.h>
#import <AVFoundation/AVFoundation.h>
@interface OtamaAudio:NSObject
@property(nonatomic)float masterVolume;@property(nonatomic)int octave;@property(nonatomic,readonly)BOOL instrumentActive;
-(BOOL)start:(NSError**)error;-(void)stop;-(void)setPitch:(float)pitch mouth:(float)mouth active:(BOOL)active;-(void)playMelodyIndex:(NSInteger)index;-(void)stopMelody;-(void)playUISoundNamed:(NSString*)name;
@end
