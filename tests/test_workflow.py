"""Smoke tests for the SatisfyForge zero-cost content workflow."""
import json, pathlib, subprocess, sys, tempfile, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
def run(*args):
    return subprocess.run([sys.executable,*map(str,args)],cwd=ROOT,capture_output=True,text=True,check=True)
class WorkflowTest(unittest.TestCase):
    def test_draft_approval_queue(self):
        with tempfile.TemporaryDirectory() as d:
            db=pathlib.Path(d)/'test.db';out=pathlib.Path(d)/'queue.json'
            run(ROOT/'tools/library.py','--db',db,'add-asset','--kind','social','--title','Original demo','--body','Illustrative demo; no claimed results.')
            run(ROOT/'tools/build_queue.py','--db',db,'--out',out)
            self.assertEqual(json.loads(out.read_text())['posts'],[])
            run(ROOT/'tools/library.py','--db',db,'set-asset-status','--id','1','--status','approved')
            run(ROOT/'tools/build_queue.py','--db',db,'--out',out)
            posts=json.loads(out.read_text())['posts']
            self.assertEqual(len(posts),1)
            self.assertEqual(posts[0]['title'],'Original demo')
            run(ROOT/'tools/library.py','--db',db,'set-asset-status','--id','1','--status','archived')
            run(ROOT/'tools/build_queue.py','--db',db,'--out',out)
            self.assertEqual(json.loads(out.read_text())['posts'],[])
if __name__=='__main__':unittest.main()
