"""Offline integrity check for the recovered production runtime."""
import hashlib,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parent
def ensure_software():
    expected=json.loads((ROOT/'Runtime_Integrity.json').read_text())
    for name,checksum in expected.items():
        path=ROOT/name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=checksum:
            raise ValueError('Production runtime integrity failure: '+name)
    return True
if __name__=='__main__':
    ensure_software()
    print('Production runtime integrity passed')
