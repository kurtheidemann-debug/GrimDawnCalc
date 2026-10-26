"""Refresh normalized optimizer inputs from a local Grim Dawn installation."""
import argparse,json,pathlib,subprocess,shutil,struct,hashlib
from reagents import Reader
root=pathlib.Path(__file__).resolve().parent
def main():
 p=argparse.ArgumentParser();p.add_argument('--game',required=True,type=pathlib.Path);p.add_argument('--save',required=True,type=pathlib.Path);p.add_argument('--out',required=True,type=pathlib.Path);p.add_argument('--java',default='java');p.add_argument('--character',default='Mal');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 subprocess.run([a.java,'-Xmx3g','-cp',str(root/'gd-edit-standalone.jar'),'clojure.main',str(root/'extract_data.clj'),str(a.game),str(a.save),str(a.out),a.character],check=True)
 material=[]
 for name in ['reagents.gst','potions.gst']:
  r=Reader((a.save/name).read_bytes());magic=r.u();block=r.u();size=r.u(False);start=r.p;version=r.u();r.u(False);mod=r.st();count=r.u()
  if magic!=1 or block not in [20,21] or version!=1:raise ValueError('Unsupported '+name+' format; extraction stopped')
  for _ in range(count):
   r.u();length=r.u(False);pos=r.p;record=r.st();quantity=r.u() if r.p-pos<length else 1
   assert r.p-pos==length;chk=struct.unpack_from('<I',r.b,r.p)[0];r.p+=4;assert chk==r.s
   material.append({'file':name,'record':record,'quantity':quantity})
  assert r.p-start==size;chk=struct.unpack_from('<I',r.b,r.p)[0];r.p+=4;assert chk==r.s and r.p==len(r.b)
 (a.out/'materials.json').write_text(json.dumps(material))
 for name in ['guide70.json','guide83.json']:
  if (root/name).exists() and (root/name).resolve()!=(a.out/name).resolve():shutil.copy2(root/name,a.out/name)
 profile=root/'offense_profile.json'
 if profile.exists():
  data=json.loads(profile.read_text())
  if data.get('character') in [None,a.character] and (a.out/'offense_profile.json').resolve()!=profile.resolve():shutil.copy2(profile,a.out/'offense_profile.json')
 print('Refresh complete. Item IDs belong to this refreshed snapshot; do not apply IDs from an older report.')
if __name__=='__main__':main()
