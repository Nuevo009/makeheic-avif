# makeavif.py

Unless necessary, you should not use avif. The little promotion it brings is not worth what it costs.

**You may need to use [JPEG XL](https://github.com/libjxl/libjxl) which is more powerful.**
## Requirements:

1. FFmpeg & FFprobe with librav1e biult-in 
2. GPAC Mp4Box version >= 0.8.0
3. ImageMagick
## Compatibility test
* Microsoft Photos
   * After you install the AV1 Video Extension, you can view avif images in YUV444P8 or YUV420P8 format in Microsoft Photos. But it *does not support depth that is larger than 8bit.* 

   * After you install the HEVC Video Extension, you can only view YUV420P8 format heic images in Microsoft Photos. Any format other than this is not supported.

   * For both avif and heic, depending on the situation, the decoding may be incorrect. Such as when the color matrix is set to bt601, the display will have a strange color cast.

   * Additionally, for avif images created by libavif, Microsoft Photos will have a strange vertical color bar on the right side of the images when the format is set to YUV444.

   * This method is never recommended.

* Google Chrome
   * You can view avif images in any format even YUV444P12 format in google chrome. I think the correct display of avif should be based on Google Chrome.

   * Do not support heic.

* Firefox
   * Support avif, but there will be *a significant precision loss when depth>=10*, so this method is not recommended.

   * Do not support heic.

* XnviewMp, Gimp, and ImageGlass can view them normally, *but because of their different implementations, the display between different platforms is not always the same.*

* The alpha plane that mp4box made cannot be recognized by libavif and any libheif based decoders like ImageMagick, FFmpeg, XnviewMp, Gimp, ImageGlass. About XnviewMp, the display is correct. You just can't view the alpha channel separately. *But ImageGlass cannot open the image made by mp4box with alpha channel .*

* Some mobile device cannot recognize heic and avif images made by mp4box.

* Considering about the compatibility, using [libheif](https://github.com/strukturag/libheif) or [libavif](https://github.com/AOMediaCodec/libavif) is more appropriate. You may find some useful method [here](https://amefs.net/archives/2221.html#:~:text=%E8%AF%86%E5%88%AB%E7%9A%84%E9%97%AE%E9%A2%98%E3%80%82-,%E4%BD%BF%E7%94%A8%20libheif,-%E5%AE%89%E8%A3%85%E7%8E%AF%E5%A2%83).

## Simple efficiency summary

* Encoding speed: heic >> avif

* Memory usage: heic << avif

* CPU usage: heic >> avif 

* Compression rate: avif > heic

* Decoding speed : heic >> avif 


***
# makeheic.py
A crappy script that uses ffmpeg &amp; mp4box to convert pictures to heic.

~Yeah now I'm actually making it more than just a .bat file.~

## Requirements:
1. FFmpeg & FFprobe with libx265 biult-in.
2. Mp4box (if you need to use alpha channel & icc you may need dev version, for the moment)
3. ImageMagick (not necessary if you don't care about icc)

## Usage:
1. Drag and drop (will use default settings).
2. Command line
