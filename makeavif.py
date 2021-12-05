import os,sys
import argparse
import subprocess
import re
from random import choice

class args:
    pass



class makeavif:
    def __init__(self,in_fp,out_fp,q=80,speed=4,delsrc=False,sws=False,alpha=False,noalpha=False,noicc=False,mat=None,depth=10,sample='444',pid=choice(range(1000,10000))):
        self.in_fp = in_fp
        self.out_fp = out_fp
        self.q = q
        self.speed = speed
        self.delsrc = delsrc
        self.sws = sws
        self.alpha = alpha
        self.noalpha = noalpha
        self.noicc = noicc
        self.mat = mat
        self.depth = depth
        self.sample=sample
        self.pid = pid
        if sample == '444':
            self.subs_w=0
            self.subs_h=0
        elif sample == '422':
            self.subs_w=1
            self.subs_h=0
        elif sample == '420':
            self.subs_w=1
            self.subs_h=1
        else:
            raise TypeError('output subsampling not supported.')
        if depth == 10:
            self.bits=10
        elif depth == 8:
            self.bits=8
        elif depth == 12:
            self.bits=12
        else:
            raise TypeError('output bitdepth not supported')

    def run_probe(self):
        if not self.noicc:
            self.hasicc = not subprocess.run(r'magick "{INP}" "{OUT}.{PID}.icc"'.format(INP=self.in_fp,OUT=r'%temp%\make.avif',PID=self.pid),shell=True).returncode
        else:
            self.hasicc = False

        probe = subprocess.Popen(r'ffprobe -hide_banner -i "{INP}"'.format(INP=self.in_fp),shell=True,   stderr=subprocess.PIPE)
        probe_result = probe.stderr.read().decode()

        #Use extra characters to hopefully ensure that it's grabbing what I want.
        self.probe_codec = re.search('Video: [a-z0-9A-Z]+',probe_result,re.M).group()
        #I'm kinda lazy, feel free to add whatever ffmpeg supports.
        if not self.probe_codec[7:] in ('webp','png','mjpeg','bmp','ppm','tiff'): 
            raise TypeError(r'input file "{INP}" codec not supported.'.format(INP=in_fp))

        self.probe_pixfmt = re.search(', yuv|, [a]*rgb[albepf0-9]*|, [a]*bgr[albepf0-9]*|, [a]*gbr[albepf0-9]*|, pal8|, gray|, ya',probe_result)
        self.probe_alpha = re.search('yuva4|argb|bgra|rgba|gbra|ya[81]',probe_result)
        if not self.probe_pixfmt:
            raise TypeError(r'input file "{INP}" pixel format not supported.'.format(INP=in_fp))
        else:
            self.probe_pixfmt = self.probe_pixfmt.group()
        probe_sub = None
        probe_mat = False

        if self.probe_pixfmt == ', yuv':
            probe_sub = re.search('4[4210]+p',probe_result).group(0)
            probe_mat = re.search('bt470bg|bt709',probe_result)

        if probe_sub in ['444p',None]:
            self.probe_subs_w=0
            self.probe_subs_h=0
        elif probe_sub == '422p':
            self.probe_subs_w=1
            self.probe_subs_h=0
        else:
            self.probe_subs_w=1
            self.probe_subs_h=1

        if probe_mat and self.mat==None:
            self.mat_l=('smpte170m' if probe_mat.group(0)=='bt470bg' else 'bt709')
            self.mat_s=('170m' if probe_mat.group(0)=='bt470bg' else '709')
        else:
            self.mat_l=('smpte170m' if self.mat=='bt601' else 'bt709')
            self.mat_s=('170m' if self.mat=='bt601' else '709')

        probe_resolution = re.search('[0-9]+x[0-9]+',probe_result).group(0).split('x')
        self.probe_res_w=int(probe_resolution[0])
        self.probe_res_h=int(probe_resolution[1])
        self.probe_w_odd = self.probe_res_w % 2
        self.probe_h_odd = self.probe_res_h % 2

    def cmd_line_gen(self):
        icc_opt = r':icc_path=make.avif.{PID}.icc'.format(PID=self.pid) if self.hasicc else ''
        #Use padding if output is subsampled and image w/h not mod by 2
        pad_w=self.probe_w_odd and self.subs_w
        pad_h=self.probe_h_odd and self.subs_h
        if pad_w or pad_h:
            pad = 'pad={W}:{H},'.format(W=self.probe_res_w+pad_w, H=self.probe_res_h+pad_h)
        else:
            pad = ''
        #Use swscale to handle weird "subsampled but not mod by 2" images, and use zimg for better  conversion if there's no chroma re-subsampling.
        c_resubs = (self.probe_subs_w != self.subs_w) or (self.probe_subs_h != self.subs_h)
        if c_resubs or self.sws:
            scale_filter = r'scale=out_range=pc:flags=spline:sws_dither=ed:out_v_chr_pos={VC}:out_h_chr_pos={HC}:out_color_matrix={MAT_L}'.format(MAT_L=self.mat_l,VC=(127 if self.subs_h else 0),HC=(127 if self.subs_w else 0))
        else:
            scale_filter = r'zscale=r=pc:f=spline36:d=error_diffusion:c=1:m={MAT_S}'.format(MAT_S=self.mat_s)
        ff_pixfmt='yuv{S}p{D}'.format(S=self.sample,D=(str(self.bits) if self.bits>8 else '')) + ('le' if self.bits>8 else '')
        ff_pixfmt_a='gray{D}'.format(D=(str(self.bits) if self.bits>8 else '')) + ('le' if self.bits>8 else '')
        coffs = (-2 if self.subs_w and self.subs_h else 1)
        # Actually the color_primaries should be IEC 61966-2-1 (aka sRGB or sYCC), but ffmpeg does not accept this value. And at least for color_primaries, bt709 strictly equal to IEC 61966-2-1 ,so it is chosen.
        self.ff_cmd_img=r'ffmpeg -hide_banner -r 1 -i "{INP}" -vf {PD}{SF},format={PF} -qp {QP} -frames 1 -c:v libsvtav1 -tile-columns 2 -tile-rows 2 -color_range pc -color_trc iec61966-2-1 -color_primaries bt709 -preset {S} "%temp%\make.avif.{PID}.ivf" -y'.format(QP=self.q,S=self.speed,INP=self.in_fp,PD=pad,SF=scale_filter,MAT_L=self.mat_l,PF=ff_pixfmt,PID=self.pid)

        self.m4b_cmd_img=r'cd /d %temp% && mp4box -add-image "make.avif.{PID}.ivf":primary:image-size={WxH}{ICC} -brand avif -new "{OUT}" && del "make.avif.{PID}.ivf"'.format(OUT=self.out_fp,ICC=icc_opt,PID=self.pid,WxH=str(self.probe_res_w)+'x'+str(self.probe_res_h))

        self.ff_cmd_a=r'ffmpeg -hide_banner -r 1 -i "{INP}" -vf {PD}extractplanes=a,format={PF} -qp {QP} -frames 1 -c:v libsvtav1 -tile-columns 2 -tile-rows 2 -color_range pc -color_trc iec61966-2-1 -color_primaries bt709 -preset {S} "%temp%\make.avif.alpha.{PID}.ivf" -y'.format(QP=self.q,S=self.speed,INP=self.in_fp,PD=pad,SF=':'.join(scale_filter.split(':')[:-1]),MAT_L=self.mat_l,PF=ff_pixfmt_a,PID=self.pid)

        self.m4b_cmd_a=r'cd /d %temp% && mp4box -add-image "make.avif.{PID}.ivf":primary:image-size={WxH}{ICC}  -add-image "make.avif.alpha.{PID}.ivf":ref=auxl,1:alpha:image-size={WxH} -brand avif -new "{OUT}" && del "make.avif.alpha.{PID}.ivf"'.format(OUT=self.out_fp,PID=self.pid,ICC=icc_opt,WxH=str(self.probe_res_w)+'x'+str(self.probe_res_h))

    def encode(self):
        subprocess.run(self.ff_cmd_img,shell=True)
        if (self.probe_alpha or self.alpha) and not self.noalpha:
            subprocess.run(self.ff_cmd_a,shell=True)
            subprocess.run(self.m4b_cmd_a,shell=True)
        else:
            subprocess.run(self.m4b_cmd_img,shell=True)
        if self.hasicc:
            subprocess.run(r'del %temp%\make.avif.{PID}.icc'.format(PID=self.pid),shell=True)
        #Delete source file or not?
        if self.delsrc:
            os.remove(self.in_fp)

    def make(self):
        self.run_probe()
        self.cmd_line_gen()
        self.encode()




if __name__ == '__main__':
    #Arguments, ordinary stuff I guess.
    parser = argparse.ArgumentParser(description='avif encode script using ffmpeg & mp4box.',formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-q',type=int,required=False,help='Quality(cqp),range(0-255), default 80.',default=80)
    parser.add_argument('-speed',type=int,required=False,help='Speed level (0 is best quality, 10 is fastest) default 4',default=4)
    parser.add_argument('-o',type=str,required=False,help='Output(s), default input full name (ext. incl.) + ".avif".',nargs='*')
    parser.add_argument('-s',required=False,help='Silent mode, disables "enter to exit".',action='store_true')
    parser.add_argument('--delete-src',required=False,help='Delete source file switch, add this argument means "ON".',action='store_true')
    parser.add_argument('--sws',required=False,help='Force to use swscale switch.',action='store_true')
    parser.add_argument('--alpha',required=False,help='Force to try to encode alpha plane switch.',action='store_true')
    parser.add_argument('--no-alpha',required=False,help='Ignore alpha plane switch.',action='store_true')
    parser.add_argument('--no-icc',required=False,help='Ignore icc profile of source image switch.',action='store_true')
    #New version of libheif seems to decode with matrixs accordingly, so I think it's better to use modern bt709 as default.
    parser.add_argument('--mat',type=str,required=False,help='Matrix used to convert RGB input file, should be either bt709 or bt601 currently. If a input file is in YUV, it\'s original matrix will be "preserved". ',default=None)
    parser.add_argument('--depth',type=int,required=False,help='Bitdepth for avif-yuv output, default 10.',default=10)
    parser.add_argument('--sample',type=str,required=False,help='Chroma subsumpling for avif-yuv output, default "444"',default='444')
    parser.add_argument('INPUTFILE',type=str,help='Input file.',nargs='+')
    parser.parse_args(sys.argv[1:],args)
    pid = os.getpid()

    #If you drop a bunch of files to this script this should supposedly work fine.
    if (args.o != None) and (len(args.INPUTFILE) != len(args.o)):
        raise TypeError('the number of input and output should match if output is specified.')
    i=0
    for in_fp in args.INPUTFILE:
        in_fp = os.path.abspath(in_fp)
        if args.o == None:
            out_fp = in_fp + '.avif'
        else:
            out_fp = args.o[i]
            i+=1
        out_fp = os.path.abspath(out_fp)
        avif = makeavif(in_fp,out_fp,args.q,args.speed,args.delete_src,args.sws,args.alpha,args.no_alpha,args.no_icc,args.mat,args.depth,args.sample,pid)
        avif.make()
        
    if not args.s:
        input('enter to exit.')
