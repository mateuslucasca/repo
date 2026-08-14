#pragma once
#import <Foundation/Foundation.h>
#import <CoreGraphics/CoreGraphics.h>
#include <stdbool.h>
#ifdef __cplusplus
extern "C" {
#endif
typedef struct { bool active; bool began; bool moved; bool ended; int identifier; float x,y; float prevX,prevY; float beginX,beginY; } ACRCursor;
void ACRInitialize(void); void ACRReset(void); void ACRBegin(int,float,float); void ACRMove(int,float,float); void ACREnd(int,float,float); const ACRCursor *ACRGetCursor(int); void ACRSetAcc(float,float,float); float ACRGetAccX(void); float ACRGetAccY(void); float ACRGetAccZ(void); void ACRSetRatio(float); bool ACRIsMoved(int); bool ACRIsTouchOn(int); bool ACRIsTouchOff(int); void ACRUpdate(void);
float GetPitch(int octave,int note); void GetScale(int *octave,int *note,int whiteWidth,int blackWidth,float position,float origin);
typedef struct { float volume; int octave; bool followMode; bool hideFukidashi; int skin; bool recordHoldMode; } OtamaSettings;
void SettingInitialize(void); void SettingSave(void); const OtamaSettings *SettingState(void); void SettingSetVolume(float); void SettingSetOctave(int); void SettingSetFollow(bool); void SettingSetHideFukidashi(bool); void SettingSetSkin(int); void SettingSetRecordHoldMode(bool); float SettingGetVolume(void); int SettingGetOctave(void); bool SettingIsFollow(void); int SettingGetSkin(void);
#ifdef __cplusplus
}
#endif
