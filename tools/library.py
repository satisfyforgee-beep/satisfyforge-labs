#!/usr/bin/env python3
"""Local-first SatisfyForge library: SQLite, no dependencies or paid APIs."""
import argparse, sqlite3, json, datetime, pathlib

def connect(path):
    pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
    db=sqlite3.connect(path)
    db.execute('CREATE TABLE IF NOT EXISTS assets (id INTEGER PRIMARY KEY, kind TEXT NOT NULL, title TEXT NOT NULL, body TEXT NOT NULL, status TEXT NOT NULL DEFAULT "draft", created_utc TEXT NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS leads (id INTEGER PRIMARY KEY, source TEXT NOT NULL, company TEXT NOT NULL, contact TEXT, status TEXT NOT NULL DEFAULT "new", notes TEXT NOT NULL DEFAULT "", created_utc TEXT NOT NULL)')
    db.commit()
    return db

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--db',default='data/satisfyforge.db')
    sub=p.add_subparsers(dest='cmd',required=True)
    a=sub.add_parser('add-asset')
    for key in ('kind','title','body'): a.add_argument('--'+key,required=True)
    l=sub.add_parser('add-lead')
    for key in ('source','company'): l.add_argument('--'+key,required=True)
    l.add_argument('--contact',default='')
    l.add_argument('--notes',default='')
    approval=sub.add_parser('set-asset-status')
    approval.add_argument('--id',type=int,required=True)
    approval.add_argument('--status',choices=['draft','approved','archived'],required=True)
    q=sub.add_parser('list')
    q.add_argument('--type',choices=['assets','leads'],required=True)
    q.add_argument('--status')
    e=sub.add_parser('export')
    e.add_argument('--type',choices=['assets','leads'],required=True)
    args=p.parse_args()
    db=connect(args.db)
    now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    if args.cmd=='add-asset':
        db.execute('INSERT INTO assets(kind,title,body,created_utc) VALUES(?,?,?,?)',(args.kind,args.title,args.body,now))
        db.commit()
        print('Asset saved')
    elif args.cmd=='set-asset-status':
        cur=db.execute('UPDATE assets SET status=? WHERE id=?',(args.status,args.id))
        db.commit()
        print('Asset status updated' if cur.rowcount else 'Asset not found')
    elif args.cmd=='add-lead':
        db.execute('INSERT INTO leads(source,company,contact,notes,created_utc) VALUES(?,?,?,?,?)',(args.source,args.company,args.contact,args.notes,now))
        db.commit()
        print('Lead saved')
    else:
        table=args.type
        sql=f'SELECT * FROM {table}'
        params=[]
        if args.cmd=='list' and args.status:
            sql+=' WHERE status=?'
            params.append(args.status)
        sql+=' ORDER BY id DESC'
        db.row_factory=sqlite3.Row
        print(json.dumps([dict(x) for x in db.execute(sql,params)],indent=2))
if __name__=='__main__':
    main()
