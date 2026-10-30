#!/usr/bin/env python3
"""List or restore preserved files directly to a user-selected drive, without a cache.

Default is read-only. Downloading requires --resource, --destination and --download.
Keep recovery-manifest.json beside this script. Uses only Python's standard library.
Private GenBio downloads need HF_TOKEN in the environment, or use the website.
"""
import argparse,gzip,hashlib,json,os,pathlib,shutil,sys,tarfile,time,urllib.parse,urllib.request

class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        if urllib.parse.urlsplit(newurl).scheme!='https':raise ValueError('Refusing an insecure download redirect')
        redirected=super().redirect_request(req,fp,code,msg,headers,newurl)
        if redirected and urllib.parse.urlsplit(req.full_url).netloc!=urllib.parse.urlsplit(newurl).netloc:
            redirected.remove_header('Authorization')
        return redirected

def file_hash(path,size,algorithm):
    h=hashlib.sha256() if algorithm=='sha256' else hashlib.sha1() if algorithm=='sha1' else hashlib.sha1(b'blob '+str(size).encode()+b'\0')
    with path.open('rb') as source:
        while chunk:=source.read(1024*1024):h.update(chunk)
    return h.hexdigest()

def verify_git_archive(path,row):
    """Verify source contents when a hosting service regenerates its tar wrapper."""
    entries={};expanded=0;normalizations=row.get('git_checkout_normalizations',{})
    max_expanded=row['expanded_bytes']+16*1024*1024
    def git_hash(kind,data):return hashlib.sha1(kind.encode()+b' '+str(len(data)).encode()+b'\0'+data).hexdigest()
    with path.open('rb') as raw,gzip.GzipFile(fileobj=raw) as gz:
        with tarfile.open(fileobj=gz,mode='r|') as tar:
            root=None
            for member in tar:
                first,sep,name=member.name.partition('/')
                if root is None:root=first
                if first!=root:raise RuntimeError('Unexpected source archive root')
                if not sep or not name or member.isdir():continue
                if name in entries:raise RuntimeError('Duplicate source archive member')
                if len(entries)>row.get('source_files',0)+100:raise RuntimeError('Unexpected source archive file count')
                if member.issym():digest=git_hash('blob',member.linkname.encode('utf-8','surrogateescape'));mode='120000'
                elif member.isfile():
                    expanded+=member.size
                    if expanded>max_expanded:raise RuntimeError('Expanded source archive exceeds expected budget')
                    stream=tar.extractfile(member);h=hashlib.sha1(b'blob '+str(member.size).encode()+b'\0');count=0;buffer=b''
                    expected=normalizations.get(name)
                    if expected and member.size>1_000_000:raise RuntimeError('Unexpected checkout normalization size')
                    while chunk:=stream.read(1024*1024):
                        count+=len(chunk);h.update(chunk)
                        if expected:buffer+=chunk
                    if count!=member.size:raise RuntimeError('Truncated source file')
                    digest=h.hexdigest();mode='100755' if member.mode&0o111 else '100644'
                    if expected:
                        normalized=git_hash('blob',buffer.replace(b'\r\n',b'\n'))
                        if normalized!=expected:raise RuntimeError('Source file differs from pinned Git blob')
                        digest=normalized
                else:raise RuntimeError('Unsupported source archive member')
                entries[name]=(mode,digest)
        padding=0
        while chunk:=gz.read(1024*1024):
            padding+=len(chunk)
            if padding>1024*1024 or any(chunk):raise RuntimeError('Unexpected data after source archive entries')
    for module in row.get('gitlinks',[]):
        name=module['path']
        if any(p==name or p.startswith(name+'/') for p in entries):raise RuntimeError('Unexpected files at a submodule path')
        entries[name]=('160000',module['sha'])
    directories={'':{}}
    for name,value in entries.items():
        pieces=name.split('/');parent=''
        for part in pieces[:-1]:
            directories.setdefault(parent,{})[part]=None;parent+=part+'/';directories.setdefault(parent,{})
        directories[parent][pieces[-1]]=value
    def tree(prefix=''):
        items=[]
        for name,value in directories[prefix].items():
            mode,digest=('40000',tree(prefix+name+'/')) if value is None else value
            encoded=name.encode('utf-8','surrogateescape')
            items.append((encoded+(b'/' if mode=='40000' else b''),mode.encode()+b' '+encoded+b'\0'+bytes.fromhex(digest)))
        return git_hash('tree',b''.join(v for _,v in sorted(items)))
    if tree()!=row['git_tree']:raise RuntimeError('Restored source tree differs from the pinned commit')
    return True

def source_plan_row(receipt,path):
    row={'path':path,'url':receipt['url'],'size':receipt['compressed_bytes'],'hash':receipt['bundle_sha256'],'algorithm':'sha256'}
    if receipt.get('expected_tree'):
        row.update(git_tree=receipt['expected_tree'],expanded_bytes=receipt['expanded_bytes'],source_files=receipt['files'],gitlinks=receipt.get('gitlinks_requiring_separate_archives',[]),git_checkout_normalizations={r['path']:r['git_blob_sha1'] for r in receipt.get('checkout_crlf_normalized_for_git_comparison',[])})
    return row

class RecoveryOpener:
    """Use IA's own replica catalog if a recorded download server is unavailable."""
    def __init__(self):self.base=urllib.request.build_opener(SafeRedirect())
    def open(self,request,timeout=90):
        try:return self.base.open(request,timeout=timeout)
        except (urllib.error.URLError,OSError) as original_error:
            url=urllib.parse.urlsplit(request.full_url)
            if not (url.hostname=='archive.org' or (url.hostname or '').endswith('.archive.org')):raise
            if isinstance(original_error,urllib.error.HTTPError) and original_error.code not in (404,500,502,503,504):raise
            parts=url.path.split('/')
            marker='download' if 'download' in parts else 'items' if 'items' in parts else None
            if not marker:raise
            pos=parts.index(marker)
            if len(parts)<=pos+2:raise
            item=parts[pos+1];filename='/'.join(parts[pos+2:])
            with self.base.open('https://archive.org/metadata/'+item,timeout=30) as response:
                metadata=json.load(response)
            if metadata.get('is_dark'):raise RuntimeError('Internet Archive item was removed; do not use replicas to bypass its restriction')
            replicas=[{'server':metadata.get(k),'dir':metadata.get('dir')} for k in ('d1','d2')]
            replicas+=metadata.get('alternate_locations',{}).get('workable',[])
            for replica in replicas:
                host=replica.get('server');folder=replica.get('dir')
                if not host or urllib.parse.urlsplit('https://'+host).hostname!=host or not host.endswith('.archive.org') or not folder or not folder.startswith('/'):continue
                target='https://'+host+folder.rstrip('/')+'/'+filename
                if target==request.full_url:continue
                headers={k:v for k,v in request.header_items() if k.lower()!='authorization'}
                try:return self.base.open(urllib.request.Request(target,headers=headers),timeout=timeout)
                except (urllib.error.URLError,OSError):continue
            raise original_error

def base_plan(resource):
    github=resource.get('verified_github_source_bundle',{})
    if github.get('status')=='verified':
        return [source_plan_row(github,resource['repo'].replace('/','--')+'--'+github['revision']+'.tar.gz')]
    copy=resource.get('created_remote_copy')
    if copy and resource.get('kind')!='github':
        prefix='https://huggingface.co/'+('datasets/' if copy.get('repo_type')=='dataset' else '')+copy['destination']+'/resolve/'+copy['destination_revision']+'/'
        return [{'path':f['rfilename'],'url':prefix+urllib.parse.quote(f['rfilename'],safe='/'),'size':f['size'],'hash':f.get('lfs',{}).get('sha256') or f['blobId'],'algorithm':'sha256' if f.get('lfs') else 'git-blob-sha1','private':copy.get('private',False)} for f in resource['files']]
    if resource.get('repo')=='secemp9/arxiv-complete':
        # This pinned independent mirror passed all 3,749 metadata and retrieval checks.
        prefix='https://huggingface.co/datasets/ml-resources/arxiv-complete/resolve/116f98d3d8e8727730747a779a213234fc3ad145/'
        return [{'path':f['rfilename'],'url':prefix+urllib.parse.quote(f['rfilename'],safe='/'),'size':f['size'],'hash':f.get('lfs',{}).get('sha256') or f['blobId'],'algorithm':'sha256' if f.get('lfs') else 'git-blob-sha1'} for f in resource['files']]
    ia=resource.get('internet_archive_copy',{})
    if ia.get('status')=='verified' and ia.get('currently_available',True):
        url=ia['archive_url'];return [{'path':url.rsplit('/',1)[-1],'url':url,'size':ia['bytes'],'hash':ia['archive_hashes']['sha256'],'algorithm':'sha256'}]
    source=resource.get('verified_source_bundle',{})
    if source.get('status')=='verified':
        return [source_plan_row(source,resource['repo'].replace('/','--')+'.tar.gz')]
    archived=resource.get('verified_archived_files',[])
    if archived and len(archived)==len(resource.get('files',archived)):
        return [{'path':f['name'],'url':f['archive_url'],'size':f['size'],'hash':f.get('sha256') or f.get('expected_sha256') or f['archive_sha1'],'algorithm':'sha256' if f.get('sha256') or f.get('expected_sha256') else 'sha1'} for f in archived]
    return []

def plan(resource):
    rows=base_plan(resource)
    dependencies=resource.get('submodule_recovery',{})
    covered_trees=set()
    for receipt in dependencies.get('github_bundles',[]):
        if receipt.get('status')!='verified':continue
        rows.append(source_plan_row(receipt,'dependencies/'+receipt['original_repo'].replace('/','--')+'--'+receipt['revision']+'.tar.gz'))
        covered_trees.add(receipt['expected_tree'])
    for receipt in dependencies.get('archive_file_receipts',{}).values():
        if receipt.get('status')!='verified' or not receipt.get('currently_available',True):continue
        if receipt.get('git_tree') in covered_trees:continue
        url=receipt['archive_url']
        rows.append({'path':'dependencies/'+url.rsplit('/',1)[-1],'url':url,'size':receipt['bytes'],'hash':receipt['archive_hashes']['sha256'],'algorithm':'sha256'})
        if receipt.get('git_tree'):covered_trees.add(receipt['git_tree'])
    for receipt in dependencies.get('nested_archived_checks',[]):
        if receipt.get('status')!='verified' or receipt.get('expected_tree') in covered_trees:continue
        rows.append(source_plan_row(receipt,'dependencies/'+receipt['repo'].replace('/','--')+'--'+receipt['expected_tree']+'.tar.gz'))
    return rows

def resource_id(resource):
    return resource.get('kind','resource')+':'+resource.get('repo',resource['name'])

def missing_dependencies(resource):
    dependencies=resource.get('submodule_recovery',{})
    covered={r['expected_tree'] for r in dependencies.get('github_bundles',[])+dependencies.get('nested_archived_checks',[]) if r.get('status')=='verified'}
    covered.update(r.get('git_tree') for r in dependencies.get('archive_file_receipts',{}).values() if r.get('status')=='verified' and r.get('currently_available',True))
    return [r for r in dependencies.get('required_archives',[]) if r['git_tree'] not in covered]

def download(row,destination,opener):
    target=(destination/row['path']).resolve()
    if not target.is_relative_to(destination):raise ValueError('Unsafe manifest path')
    target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():
        if target.stat().st_size==row['size'] and file_hash(target,row['size'],row['algorithm'])==row['hash']:
            print('Already verified:',row['path']);return
        if row.get('git_tree') and verify_git_archive(target,row):print('Already verified source tree:',row['path']);return
        raise RuntimeError('Existing file differs; move it aside before retrying: '+row['path'])
    partial=target.with_name(target.name+'.part')
    if partial.is_symlink():raise ValueError('Refusing symlink partial file')
    if row['size']==0 and not partial.exists():partial.touch(exist_ok=False)
    for attempt in range(4):
        offset=partial.stat().st_size if partial.exists() else 0
        if row.get('git_tree') and offset:
            # Generated source archives may not support ranges or stable wrappers.
            # Restart this helper's partial archive; completed files stay untouched.
            with partial.open('wb'):pass
            offset=0
        if offset>row['size']:raise RuntimeError('Partial file larger than expected')
        if offset==row['size']:break
        max_size=row['size']+16*1024*1024 if row.get('git_tree') else row['size']
        if shutil.disk_usage(destination).free<max_size-offset+16*1024*1024:raise RuntimeError('Insufficient free space on selected drive')
        headers={'Accept-Encoding':'identity','User-Agent':'FreePreservationRestore/1.0'}
        if offset:headers['Range']=f'bytes={offset}-'
        if row.get('private'):
            token=os.environ.get('HF_TOKEN')
            if not token:raise RuntimeError('Private repository: set HF_TOKEN or sign into Hugging Face and download through the website')
            headers['Authorization']='Bearer '+token
        try:
            with opener.open(urllib.request.Request(row['url'],headers=headers),timeout=90) as response:
                encoded=response.headers.get('Content-Encoding','').lower()=='gzip'
                if offset and encoded:raise RuntimeError('Compressed HTTP response cannot be resumed; remove the small .part file and retry')
                if offset:
                    expected=f"bytes {offset}-{row['size']-1}/{row['size']}"
                    if response.status!=206 or response.headers.get('Content-Range')!=expected:raise RuntimeError('Server did not honor resume range; partial file retained')
                elif response.status!=200:raise RuntimeError('Unexpected HTTP response')
                with partial.open('ab' if offset else 'wb') as sink:
                    count=offset
                    stream=gzip.GzipFile(fileobj=response) if encoded else response
                    while chunk:=stream.read(1024*1024):
                        if count+len(chunk)>max_size:raise RuntimeError('Response exceeds expected size budget')
                        sink.write(chunk);count+=len(chunk)
                if count!=row['size'] and not row.get('git_tree'):raise OSError('Incomplete download')
            break
        except urllib.error.HTTPError as exc:
            if exc.code==429:raise RuntimeError('Service rate limit reached; retry after '+exc.headers.get('Retry-After','the service cooldown')+' seconds. Partial file retained.') from None
            if 400<=exc.code<500:raise RuntimeError('Download unavailable or access required (HTTP '+str(exc.code)+'). Partial file retained.') from None
            if attempt==3:raise RuntimeError('Service error; rerun to resume (HTTP '+str(exc.code)+')') from None
            time.sleep(min(2**attempt,8))
        except (OSError,urllib.error.URLError) as exc:
            if attempt==3:raise RuntimeError('Download interrupted; rerun to resume. Error type: '+type(exc).__name__) from None
            time.sleep(min(2**attempt,8))
    if file_hash(partial,partial.stat().st_size,row['algorithm'])!=row['hash']:
        if not row.get('git_tree'):raise RuntimeError('Checksum mismatch; partial file retained for inspection: '+row['path'])
        verify_git_archive(partial,row)
        print('Pinned source tree verified; compressed archive packaging changed:',row['path'])
    partial.rename(target);print('Verified:',row['path'])

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=pathlib.Path,default=pathlib.Path(__file__).with_name('recovery-manifest.json'))
    parser.add_argument('--list',action='store_true');parser.add_argument('--resource');parser.add_argument('--destination',type=pathlib.Path);parser.add_argument('--download',action='store_true')
    a=parser.parse_args()
    if not a.manifest.exists() and a.manifest.name=='recovery-manifest.json':
        candidates=list(a.manifest.parent.glob('recovery-manifest-*.json'))
        if len(candidates)==1:a.manifest=candidates[0]
        elif candidates:raise RuntimeError('Multiple manifests found; choose one with --manifest')
    m=json.loads(a.manifest.read_text());resources=sum((m.get(k,[]) for k in ['resources','supplementary_resources','supporting_source_resources','archived_weight_resources','historical_collection_resources']),[])
    if not a.resource:
        for r in resources:
            if r.get('kind')=='torrent':
                print(f"{resource_id(r)}\t{r['files']} torrent files\t{r['dataset_bytes']:,} bytes\tUse the saved torrent with Transmission; see QUICKSTART.md. {r['scope']}")
                continue
            files=plan(r);gaps=missing_dependencies(r)
            status=f"PARTIAL: {len(gaps)} required submodule archives unavailable" if gaps else r.get('scope','')
            print(f"{resource_id(r)}\t{len(files)} files\t{sum(f['size'] for f in files):,} bytes\t{status}")
        return
    matches=[r for r in resources if a.resource in [resource_id(r),r.get('repo'),r['name']]]
    if len(matches)!=1:raise RuntimeError('Choose an exact resource identifier from --list'+(': '+', '.join(resource_id(r) for r in matches) if matches else ''))
    if matches[0].get('kind')=='torrent':
        r=matches[0]
        print(f"Torrent: {r['metadata_filename']}; {r['files']} files, {r['dataset_bytes']:,} bytes. Info hash: {r['info_hash']}")
        print('Nothing downloaded. Open the saved torrent in Transmission, choose the external drive before starting, and follow QUICKSTART.md. This helper does not start torrents.')
        print(r['scope'])
        return
    files=plan(matches[0])
    if not files:raise RuntimeError('No verified exact recovery plan is available for this resource; consult the recovery index')
    print(f"Plan: {len(files)} files, {sum(f['size'] for f in files):,} bytes")
    gaps=missing_dependencies(matches[0])
    if gaps:
        print('Incomplete source recovery: '+str(len(gaps))+' required submodule archives are not currently available.')
        for gap in gaps:print('Missing:',gap['repo'],gap['revision'],', '.join(gap['install_paths']))
        if a.download:raise RuntimeError('Download not started: update the recovery kit after the remaining submodule copies are verified. The main archive alone is incomplete.')
    if not a.download:
        print('Nothing downloaded. Add --download and --destination pointing to your external drive when ready.');return
    if not a.destination:raise RuntimeError('--destination is required; no default local cache is used')
    destination=a.destination.expanduser().resolve();destination.mkdir(parents=True,exist_ok=True)
    opener=RecoveryOpener()
    for row in files:download(row,destination,opener)

if __name__=='__main__':
    try:main()
    except Exception as exc:sys.exit(str(exc))
