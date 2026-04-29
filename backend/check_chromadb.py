import os

try:
    import chromadb
except Exception as exc:
    print('chromadb import failed:', exc)
    raise

paths = ['/app/chromadb_store', os.path.join(os.getcwd(), 'chromadb_store')]
for p in paths:
    try:
        client = chromadb.PersistentClient(path=p)
        col = client.get_or_create_collection('researchers')
        print(f'ChromaDB documents (path={p}):', col.count())
        break
    except Exception as e:
        print(f'Failed to open chromadb at {p}:', e)
