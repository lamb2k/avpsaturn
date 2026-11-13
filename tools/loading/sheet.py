import sys, glob
from PIL import Image, ImageDraw
run=sys.argv[1]; cols=int(sys.argv[2]) if len(sys.argv)>2 else 5; first=int(sys.argv[3]) if len(sys.argv)>3 else 0; n=int(sys.argv[4]) if len(sys.argv)>4 else 20
d=f'E:/AvP/learning/lane-loading/ymir/runs/{run}/'
fs=sorted(glob.glob(d+'*.png'), key=lambda p: (0 if 'auto_' not in p else 1, p))
fs=[f for f in fs if 'sheet' not in f and 'last' not in f][first:first+n]
w,h=246,207
ims=[Image.open(f).crop((0,26,985,854)).resize((w,h)) for f in fs]
rows=(len(ims)+cols-1)//cols
s=Image.new('RGB',(w*cols,h*rows))
for k,im in enumerate(ims):
    ImageDraw.Draw(im).text((4,4),fs[k].split('/')[-1][:-4],fill=(255,255,0)); s.paste(im,((k%cols)*w,(k//cols)*h))
s.save(d+f'sheet_{first}.png'); print(len(fs))
