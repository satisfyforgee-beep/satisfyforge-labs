#!/usr/bin/env python3
"""Generate a safe publishing queue from approved assets; no direct platform API calls."""
import argparse, json, sqlite3, pathlib, datetime

def main():
 p=argparse.ArgumentParser();p.add_argument('--db',default='data/satisfyforge.db');p.add_argument('--out',default='content/queue.json');p.add_argument('--max-items',type=int,default=10);a=p.parse_args()
 if a.max_items<1: p.error('--max-items must be positive')
 db=sqlite3.connect(a.db);db.row_factory=sqlite3.Row
 rows=db.execute('SELECT id,kind,title,body FROM assets WHERE status=? ORDER BY id ASC LIMIT ?',('approved',a.max_items)).fetchall()
 queue={'generated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'review_before_platform_submission','posts':[dict(r) for r in rows]}
 path=pathlib.Path(a.out);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(queue,indent=2)+'\n',encoding='utf-8');print(f'{len(rows)} approved assets exported to {path}')
if __name__=='__main__':main()
