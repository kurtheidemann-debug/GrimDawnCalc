import struct,pathlib,json
class Reader:
 def __init__(self,b):
  self.b=b;self.p=4;self.s=struct.unpack_from('<I',b)[0]^0x55555555;self.t=[];v=self.s
  for _ in range(256):
   v=(((v>>1)|((v&1)<<31))*39916801)&0xffffffff;self.t.append(v)
 def u(self,advance=True):
  b=self.b[self.p:self.p+4];assert len(b)==4;self.p+=4;v=struct.unpack('<I',b)[0]^self.s
  if advance:
   for x in b:self.s^=self.t[x]
  return v
 def byte(self):
  x=self.b[self.p];self.p+=1;v=x^(self.s&255);self.s^=self.t[x];return v
 def st(self):
  n=self.u();assert n<1000,(n,self.p)
  return bytes(self.byte() for _ in range(n)).decode()
if __name__=='__main__':
 for name in ['reagents.gst','potions.gst']:
  r=Reader((pathlib.Path('/tmp/gd-work/219990/remote/save')/name).read_bytes())
  print(name,r.u(),r.u(),r.u(False),r.u(),r.u(False),r.st(),r.u())
  print('entry',r.u(),r.st(),r.u())
  print('next ints',[r.u() for _ in range(3)])
