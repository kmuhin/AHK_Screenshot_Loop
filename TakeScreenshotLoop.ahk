; Автоматические скриншоты до двух мониторов.
#Persistent

; https://doggy8088.github.io/AutoHotkeyDocs/docs/misc/DPIScaling.htm
; To enable per-monitor DPI awareness, call the following function prior to using functions that are normally affected by DPI scaling:
DllCall("SetThreadDpiAwarenessContext", "ptr", -3, "ptr")

; Корневая директория скриншотов
DIR_DST := "sshots\"
; период скриншотов в миллисекундах
LOOP_TIMEOUT := 10000
; тип изображение (расширение файла скриншота)
; может быть .jpg, .png, .bmp и т.д.
IMAGE_EXT := ".jpg"

Loop {
; Кол-во мониторов
SysGet MonCount, MonitorCount
; Параметры монитора 1
SysGet Mon1, Monitor, 1
Mon1W := Mon1Right + Mon1Left

if (MonCount = 2) { 
    ; Параметры монитора 2
    SysGet Mon2, Monitor, 2
    Mon2W := Mon2Right + Mon2Left
    FullWidth := ABS(Mon1W - Mon2W)
    FullHeight := Max(Mon1Bottom,Mon2Bottom)
	Left := Min(Mon1Left, Mon2Left)
} else {
    FullWidth := Mon1Right
    FullHeight := Mon1Bottom
	Left := 0
}
    ; Поддиректория с датой
    dname := DIR_DST . A_YYYY . "-" . A_MM . "-" . A_DD
    FileCreateDir, %dname%
    ; имя файла "shot 2025-12-18 130506.jpg"
	fname:=( dname "\shot " A_YYYY "-" A_MM "-" A_DD " " A_Hour A_Min A_Sec IMAGE_EXT)
	; MsgBox, %fname%
	SaveScreenshotToFile(Left, 0, FullWidth, FullHeight, fname)
    Sleep, %LOOP_TIMEOUT%
}

SaveScreenshotToFile(x, y, w, h, filePath)
{
	hBitmap := GetHBitmapFromScreen(x, y, w, h)
	gdip := new GDIplus
	pBitmap := gdip.BitmapFromHBitmap(hBitmap)
	DllCall("DeleteObject", Ptr, hBitmap)
	gdip.SaveBitmapToFile(pBitmap, filePath)
	gdip.DisposeImage(pBitmap)
}

GetHBitmapFromScreen(x, y, w, h)
{
	hDC := DllCall("GetDC", Ptr, 0, Ptr)
	hBM := DllCall("CreateCompatibleBitmap", Ptr, hDC, Int, w, Int, h, Ptr)
	pDC := DllCall("CreateCompatibleDC", Ptr, hDC, Ptr)
	oBM := DllCall("SelectObject", Ptr, pDC, Ptr, hBM, Ptr)
	DllCall("BitBlt", Ptr, pDC, Int, 0, Int, 0, Int, w, Int, h, Ptr, hDC, Int, x, Int, y, UInt, 0x00CC0020)
	DllCall("SelectObject", Ptr, pDC, Ptr, oBM)
	DllCall("DeleteDC", Ptr, pDC)
	DllCall("ReleaseDC", Ptr, 0, Ptr, hDC)
	Return hBM
}

class GDIplus   {
	__New()  {
		if !DllCall("GetModuleHandle", Str, "gdiplus", Ptr)
			DllCall("LoadLibrary", Str, "gdiplus")
		VarSetCapacity(si, A_PtrSize = 8 ? 24 : 16, 0), si := Chr(1)
		DllCall("gdiplus\GdiplusStartup", PtrP, pToken, Ptr, &si, Ptr, 0)
		this.token := pToken
	}
	__Delete()  {
		DllCall("gdiplus\GdiplusShutdown", Ptr, this.token)
		if hModule := DllCall("GetModuleHandle", Str, "gdiplus", Ptr)
			DllCall("FreeLibrary", Ptr, hModule)
	}
	BitmapFromHBitmap(hBitmap, Palette := 0)  {
		DllCall("gdiplus\GdipCreateBitmapFromHBITMAP", Ptr, hBitmap, Ptr, Palette, PtrP, pBitmap)
		return pBitmap
	}
	SaveBitmapToFile(pBitmap, sOutput, Quality=75)  {
		SplitPath, sOutput,,, Extension
		if Extension not in BMP,DIB,RLE,JPG,JPEG,JPE,JFIF,GIF,TIF,TIFF,PNG
			return -1
		DllCall("gdiplus\GdipGetImageEncodersSize", UIntP, nCount, UIntP, nSize)
		VarSetCapacity(ci, nSize)
		DllCall("gdiplus\GdipGetImageEncoders", UInt, nCount, UInt, nSize, Ptr, &ci)
		if !(nCount && nSize)
			return -2
		Loop, % nCount  {
			sString := StrGet(NumGet(ci, (idx := (48+7*A_PtrSize)*(A_Index-1))+32+3*A_PtrSize), "UTF-16")
			if !InStr(sString, "*." Extension)
				continue
			pCodec := &ci+idx
			break
		}
		if !pCodec
			return -3
		if RegExMatch(Extension, "i)^J(PG|PEG|PE|FIF)$") && Quality != 75  {
			DllCall("gdiplus\GdipGetEncoderParameterListSize", Ptr, pBitmap, Ptr, pCodec, UintP, nSize)
			VarSetCapacity(EncoderParameters, nSize, 0)
			DllCall("gdiplus\GdipGetEncoderParameterList", Ptr, pBitmap, Ptr, pCodec, UInt, nSize, Ptr, &EncoderParameters)
			Loop, % NumGet(EncoderParameters, "UInt")  {
				elem := (24+A_PtrSize)*(A_Index-1) + 4 + (pad := A_PtrSize = 8 ? 4 : 0)
				if (NumGet(EncoderParameters, elem+16, "UInt") = 1) && (NumGet(EncoderParameters, elem+20, "UInt") = 6)  {
					p := elem+&EncoderParameters-pad-4
					NumPut(Quality, NumGet(NumPut(4, NumPut(1, p+0)+20, "UInt")), "UInt")
					break
				}
			}
		}
		if A_IsUnicode
			pOutput := &sOutput
		else  {
			VarSetCapacity(wOutput, StrPut(sOutput, "UTF-16")*2, 0)
			StrPut(sOutput, &wOutput, "UTF-16")
			pOutput := &wOutput
		}
		E := DllCall("gdiplus\GdipSaveImageToFile", Ptr, pBitmap, Ptr, pOutput, Ptr, pCodec, UInt, p ? p : 0)
		return E ? -5 : 0
	}
	DisposeImage(pBitmap)  {
		return DllCall("gdiplus\GdipDisposeImage", Ptr, pBitmap)
	}
}
Return