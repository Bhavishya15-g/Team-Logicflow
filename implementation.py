"""Reviewed accountability study. Run prepare, freeze, analyse and evaluate in order.
# %% sections can be read in VS Code; use the terminal for the staged workflow.
No human ratings or scientific findings are automatically manufactured.
"""
# %% M1 Dependencies and immutable study inputs
from pathlib import Path
from datetime import datetime,timezone
from io import BytesIO
import argparse,hashlib,json,os,runpy,shutil,itertools,textwrap
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from sklearn.metrics import precision_recall_fscore_support,cohen_kappa_score
BASE=Path(__file__).resolve().parent
STAGES=['design','deployment','monitoring','remediation']
COMP=['responsibility','procedure','assurance','failure_response']
LINKS=['responsibility_procedure','procedure_assurance','assurance_failure_response']
PRINCIPLES=['fairness','privacy','transparency','safety_security','accountability']

def require(ok,message):
    if not bool(ok): raise ValueError(message)
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return pd.read_csv(p,dtype=str,keep_default_na=False)
def write_once(frame,path):
    require(not path.exists(),f'Refusing to overwrite reviewed input: {path}')
    frame.to_csv(path,index=False)
def check_ids(frame,column,allowed,label,unique=True):
    require(column in frame,f'{label}: missing {column}')
    require(not unique or frame[column].is_unique,f'{label}: duplicate {column}')
    require(frame[column].ne('').all(),f'{label}: blank {column}')
    unknown=set(frame[column])-set(allowed)
    require(not unknown,f'{label}: unknown IDs BEFORE merge: {sorted(unknown)[:5]}')
def ratings(frame,columns,allowed):
    for col in columns:
        require(col in frame,f'Missing rating column {col}')
        frame[col]=pd.to_numeric(frame[col],errors='raise')
        require(frame[col].isin(allowed).all(),f'{col}: complete ratings must be in {allowed}')
    return frame

# %% M2 Prepare real corpus once and preserve full provenance

def prepare(args):
    w=args.workspace;w.mkdir(parents=True,exist_ok=True)
    marker=w/'study.json'
    if marker.exists():
        info=json.loads(marker.read_text());require(info['input_sha256']==digest(args.data),'Dataset changed; use a NEW workspace')
        print('Existing prepared study preserved:',w);return
    require(not any(w.iterdir()),'Use an empty workspace to avoid overwriting existing research files')
    old=os.environ.copy()
    try:
        os.environ['OECD_DATA_PATH']=str(args.data.resolve())
        os.environ['OECD_OUTPUT_ROOT']=str((w/'exploratory').resolve())
        for key in ['OECD_GOLD_FILE','OECD_CODER_A_FILE','OECD_CODER_B_FILE']:os.environ.pop(key,None)
        runpy.run_path(str(BASE/'exploratory.py'),run_name='__main__')
    finally:os.environ.clear();os.environ.update(old)
    pointer=json.loads((w/'exploratory/latest_run.json').read_text());source=Path(pointer['directory'])
    for name in ['answer_features_and_audit.csv','report_inventory.csv','source_row_provenance.csv','lexicon_and_stage_rules.json']:
        shutil.copy2(source/name,w/name)
    reports=read(w/'report_inventory.csv')
    e=reports[['Organization','Country']].drop_duplicates().copy()
    for col in ['canonical_id','corporate_eligible','reviewed','identity_source','decision_note']:e[col]=''
    write_once(e,w/'eligibility.csv')
    info={'input_sha256':digest(args.data),'prepared_utc':datetime.now(timezone.utc).isoformat(),
          'corpus_sha256':digest(w/'answer_features_and_audit.csv'),'reports_sha256':digest(w/'report_inventory.csv'),
          'status':'exploratory outputs only; reviewed findings pending'}
    marker.write_text(json.dumps(info,indent=2));print('NEXT: complete eligibility.csv, then run freeze')

# %% M3 Apply reviewed corporate identity before creating a permanent split

def freeze(args):
    w=args.workspace;info=json.loads((w/'study.json').read_text())
    require(not (w/'frozen.json').exists(),'Study already frozen; do not redraw review samples')
    require(digest(args.data)==info['input_sha256'],'Input changed')
    require(digest(w/'answer_features_and_audit.csv')==info['corpus_sha256'],'Prepared corpus changed')
    require(digest(w/'report_inventory.csv')==info['reports_sha256'],'Prepared report inventory changed')
    reports=read(w/'report_inventory.csv');e=read(w/'eligibility.csv')
    require(not e.duplicated(['Organization','Country']).any(),'Eligibility contains duplicate organisation-country keys')
    require(set(map(tuple,e[['Organization','Country']].values))==set(map(tuple,reports[['Organization','Country']].drop_duplicates().values)), 'Eligibility must cover every organisation-country key')
    require(e.reviewed.eq('1').all() and e.corporate_eligible.isin(['0','1']).all(),'Complete reviewed eligibility decisions 0/1')
    require(e.identity_source.ne('').all() and e.decision_note.ne('').all(),'Record identity sources and inclusion/exclusion rationale')
    included=e.loc[e.corporate_eligible.eq('1')].copy();require(len(included)>0,'No eligible corporations')
    require(included.canonical_id.ne('').all(),'Included organisations need canonical IDs, merging aliases only with evidence')
    r=reports.merge(included[['Organization','Country','canonical_id']],on=['Organization','Country'],how='inner',validate='many_to_one')
    # Manually resolve multiple aliases for the same canonical company and reporting period.
    require(not r.duplicated(['canonical_id','Reporting Period']).any(),'Multiple reports for same canonical company-period: resolve selection explicitly in eligibility/corpus before freezing')
    all_rows=read(w/'answer_features_and_audit.csv')
    a=all_rows.loc[all_rows.report_id.isin(r.report_id)&all_rows.eligible.str.lower().eq('true')].merge(r[['report_id','canonical_id']],on='report_id',validate='many_to_one')
    require(len(a)>0,'No eligible substantive answers')
    for c in COMP:
        require('original_'+c in a, 'Original dimension screening flags are missing')
        a['candidate_'+c]=a['original_'+c].str.lower().eq('true')
    a['all_four_answer']=a[['candidate_'+c for c in COMP]].all(axis=1)

    ids=sorted(r.canonical_id.unique());np.random.default_rng(42).shuffle(ids)
    pilot=set(ids[:max(1,len(ids)//4)])
    a['review_phase']=np.where(a.canonical_id.isin(pilot),'pilot','held_out')
    sample=[]
    for (phase,pred),g in a.groupby(['review_phase','all_four_answer']):
        t=g.sample(n=min(75,len(g)),random_state=42).copy()
        t['sampling_stratum']=phase+'_'+str(pred);t['population_n']=len(g);t['sample_n']=len(t);t['sample_weight']=len(g)/len(t);sample.append(t)
    design=pd.concat(sample)
    a.to_csv(w/'eligible_answers.csv',index=False);r.to_csv(w/'eligible_reports.csv',index=False)
    design[['row_id','report_id','canonical_id','review_phase','all_four_answer',*['candidate_'+c for c in COMP],'sampling_stratum','population_n','sample_n','sample_weight']].to_csv(w/'frozen_sample.csv',index=False)
    blind=design[['row_id','report_id','canonical_id','review_phase','question','answer']].copy()
    for col in COMP+LINKS+['supporting_quote','review_note']:blind[col]=''
    write_once(blind,w/'coder_A.csv');write_once(blind,w/'coder_B.csv')
    gold=blind.copy();gold['adjudication_note']='';write_once(gold,w/'adjudicated_sample.csv')
    units=pd.DataFrame(columns=['unit_id','report_id','control_id','stage','row_ids','quote',*COMP,*LINKS,'link_quote','artifact_access','artifact_url','reviewed','review_note','traceability_reference'])
    write_once(units,w/'chain_units.csv')
    coverage=pd.DataFrame(itertools.product(r.report_id,STAGES),columns=['report_id','stage'])
    for col in ['applicable','review_complete','review_scope','rationale']:coverage[col]=''
    write_once(coverage,w/'coverage.csv')
    principles=pd.DataFrame(itertools.product(r.report_id,PRINCIPLES),columns=['report_id','principle'])
    for col in ['present','row_id','quote','reviewed','rationale']:principles[col]=''
    write_once(principles,w/'principles.csv')
    frozen={'eligibility_sha256':digest(w/'eligibility.csv'),'input_sha256':info['input_sha256'],
            'locked_files':{name:digest(w/name) for name in ['eligible_answers.csv','eligible_reports.csv','frozen_sample.csv','lexicon_and_stage_rules.json']},
            'rule':'pilot/held-out groups are canonical companies, not name aliases','seed':42,'implementation_sha256':digest(BASE/'implementation.py'),'exploratory_sha256':digest(BASE/'exploratory.py')}
    (w/'frozen.json').write_text(json.dumps(frozen,indent=2));print('Frozen. Complete coding files using CODEBOOK.md; do not edit locked files.')

# %% M4 Validate all IDs and complete study coverage before accepting reviewed findings

def load_frozen(w):
    f=json.loads((w/'frozen.json').read_text())
    require(digest(BASE/'implementation.py')==f['implementation_sha256'],'Analysis code changed after freeze; version the study')
    require(digest(BASE/'exploratory.py')==f['exploratory_sha256'],'Screening code changed after freeze; version the study')
    require(digest(w/'eligibility.csv')==f['eligibility_sha256'],'Eligibility changed after freeze; create a new study version')
    for name,sha in f['locked_files'].items():require(digest(w/name)==sha,f'Frozen input changed: {name}')
    return read(w/'eligible_answers.csv'),read(w/'eligible_reports.csv'),read(w/'frozen_sample.csv')
def validate_units(w):
    a,r,design=load_frozen(w);u=read(w/'chain_units.csv');cv=read(w/'coverage.csv');p=read(w/'principles.csv')
    require(len(u)>0,'No reviewed units yet: complete chain_units.csv; no findings can be generated')
    check_ids(u,'unit_id',u.unit_id,'units');check_ids(u,'report_id',r.report_id,'units',unique=False)
    require(u.reviewed.eq('1').all() and u.stage.isin(STAGES).all(),'Complete reviewed stage codes')
    require(u.control_id.ne('').all() and not u.duplicated(['report_id','control_id','stage']).any(),'One aggregated unit per report-control-stage')
    ratings(u,COMP,[0,1,2,3]);ratings(u,LINKS,[0,1])
    require(not cv.duplicated(['report_id','stage']).any(),'Duplicate coverage records')
    require(set(zip(cv.report_id,cv.stage))==set(itertools.product(r.report_id,STAGES)),'Coverage must assess every eligible report-stage')
    require(cv.review_complete.eq('1').all() and cv.applicable.isin(['0','1']).all(),'Complete applicability and full-review decisions')
    require(cv.review_scope.ne('').all() and cv.rationale.ne('').all(),'Document scope and applicability rationale')
    applicable=set(zip(cv.loc[cv.applicable.eq('1'),'report_id'],cv.loc[cv.applicable.eq('1'),'stage']))
    require(set(zip(u.report_id,u.stage))==applicable,'Each applicable stage needs coded units; use a reviewed zero placeholder only after full review')
    source=a.set_index('row_id')
    for row in u.to_dict('records'):
        ids=row['row_ids'].split('|') if row['row_ids'] else []
        require(set(ids).issubset(source.index),'Unknown evidence row IDs')
        if ids:require(source.loc[ids,'report_id'].eq(row['report_id']).all(),'Evidence must come from the same report')
        positive=any(row[c]>0 for c in COMP+LINKS)
        if positive:
            require(bool(ids) and bool(row['quote']),'Positive ratings require a verbatim source quotation')
            joined=' '.join(source.loc[ids,'answer'])
            require(row['quote'] in joined,'Quotation not found in cited answers')
            if any(row[c] for c in LINKS):require(bool(row['link_quote']) and row['link_quote'] in joined,'Explicit links require a source quotation')
        else:require(bool(row['review_note']),'Zero units require a documented full-review note')
        if any(row[c]==3 for c in COMP):require(bool(row.get('traceability_reference','')), 'Score 3 requires an identifiable document, artifact, reference or dated record')
        require(row['artifact_access'] in ['public','internal','unclear','none'],'Specify artefact access')
        if row['artifact_access']=='public':require(row['artifact_url'].startswith('http'),'Public artefact needs a URL; reviewers must check accessibility')
    return a,r,u,cv,p

# %% M5 Publication analysis uses reviewed codes, never automatic candidate scores

def analyse(args):
    w=args.workspace;a,r,u,cv,p=validate_units(w)
    evaluation_dir=evaluate(args) # Main RQ4 requires genuine independent held-out labels.
    out=w/('reviewed_results_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir()
    registry=[]
    def table(frame,name,caption):
        frame.to_csv(out/(name+'.csv'),index=False)
        with PdfPages(out/(name+'.pdf')) as pdf:
            # Complete CSV is authoritative; readable PDF previews avoid giant evidence tables.
            for j in range(0,max(1,len(frame.columns)),5):
                g=frame.iloc[:8,j:j+5].copy()
                g=g.apply(lambda col:col.map(lambda v:'\n'.join(textwrap.wrap(textwrap.shorten(str(v),width=100,placeholder='…'),25))))
                fig,ax=plt.subplots(figsize=(11.7,8.3));ax.axis('off');ax.set_title('\n'.join(textwrap.wrap(name+' '+caption,100)),loc='left',fontsize=11)
                if len(g):
                    t=ax.table(cellText=g.values,colLabels=g.columns,loc='upper center',cellLoc='left');t.auto_set_font_size(False);t.set_fontsize(8)
                    for (i,k),cell in t.get_celld().items():
                        cell.set_height(.045 if i==0 else .14);cell.set_edgecolor('#ddd')
                        if i==0:cell.set_facecolor('#dce9ef')
                ax.text(.01,.02,'Preview of up to 8 rows; complete records and quotations are in CSV.',transform=ax.transAxes,fontsize=8)
                pdf.savefig(fig,bbox_inches='tight');plt.close(fig)
        registry.append({'id':name,'caption':caption,'kind':'table'})
    def figure(fig,frame,name,caption):
        fig.tight_layout()
        for ext in ['pdf','png']:
            buf=BytesIO();fig.savefig(buf,format=ext,dpi=300,bbox_inches='tight');require(len(buf.getvalue())>100,'Empty figure');(out/(name+'.'+ext)).write_bytes(buf.getvalue())
        frame.to_csv(out/(name+'.csv'),index=False);plt.close(fig);registry.append({'id':name,'caption':caption,'kind':'figure'})
    def heat(frame,name,caption,vmax):
        fig,ax=plt.subplots(figsize=(8,max(3,.25*len(frame))))
        im=ax.imshow(frame.to_numpy(dtype=float),vmin=0,vmax=vmax,cmap='Blues',aspect='auto');fig.colorbar(im,ax=ax)
        ax.set_xticks(range(len(frame.columns)),frame.columns,rotation=25,ha='right');ax.set_yticks(range(len(frame)),[str(v).encode('ascii','ignore').decode() for v in frame.index])
        figure(fig,frame.rename_axis('row').reset_index(),name,caption)
    u=u.merge(r[['report_id','canonical_id','Country','date','Reporting Period','template_fingerprint']],on='report_id',validate='many_to_one')
    u['strict']=100*(u[COMP].ge(2).all(axis=1)&u[LINKS].eq(1).all(axis=1)).astype(int)
    u['lenient']=100*(u[COMP].ge(1).all(axis=1)&u[LINKS].eq(1).all(axis=1)).astype(int)
    u['detail']=100*u[COMP].sum(axis=1)/12
    metrics=COMP+['strict','lenient','detail']
    stage=u.groupby(['report_id','stage'])[metrics].mean().reset_index()
    score=stage.groupby('report_id')[metrics].mean().reset_index().merge(r,on='report_id',validate='one_to_one')
    score=score.merge(a.assign(answer_words=a.answer.str.split().str.len()).groupby('report_id').answer_words.sum(),on='report_id',validate='one_to_one')
    latest=score.sort_values(['date','report_id']).groupby('canonical_id',sort=False).tail(1)
    require(len(latest)==r.canonical_id.nunique(),'An eligible company has no applicable reviewed stage')
    primary=u.loc[u.report_id.isin(latest.report_id)];sp=stage.loc[stage.report_id.isin(latest.report_id)]
    heat(latest.set_index('canonical_id')[COMP],'RQ1_F1','Reviewed mean component specificity by latest company report',3)
    fig,ax=plt.subplots();ax.scatter(latest.detail,latest.strict);ax.set(xlabel='Reviewed component detail 0–100',ylabel='Strict complete-chain rate %',xlim=(-3,103),ylim=(-3,103))
    figure(fig,latest[['canonical_id','detail','strict']],'RQ1_F2','Reviewed specificity versus explicit same-control chains')
    prevalence=pd.DataFrame([{'component':c,'code':v,'n_units':int(primary[c].eq(v).sum()),'denominator':len(primary)} for c in COMP for v in [0,1,2,3]])
    table(prevalence,'RQ1_T1','Reviewed specificity prevalence among coded primary controls')
    table(latest[['canonical_id','strict','lenient','detail']],'RQ1_T2','Specificity threshold sensitivity with all explicit links required')
    heat(sp.groupby('stage')[COMP].mean().reindex(STAGES),'RQ2_F1','Reviewed lifecycle specificity among applicable company stages',3)
    st=sp.groupby('stage').agg(rate=('strict','mean'),n_reports=('report_id','nunique')).reindex(STAGES).reset_index()
    fig,ax=plt.subplots();ax.bar(st.stage,st.rate);ax.set(ylabel='Strict chain rate %',ylim=(0,103))
    figure(fig,st,'RQ2_F2','Equal-report lifecycle rates with applicable-stage denominators')
    primary=primary.copy();primary['missing']=primary.apply(lambda row:','.join([c for c in COMP if row[c]<2]+[c for c in LINKS if row[c]==0]) or 'complete',axis=1)
    table(primary.groupby(['stage','missing']).size().rename('n_units').reset_index(),'RQ2_T1','Missing specific components and explicit links')
    controls=primary.groupby(['canonical_id','control_id','stage']).strict.max().unstack('stage').reindex(columns=STAGES)
    continuity=[]
    for s,t in zip(STAGES[:-1],STAGES[1:]):
        pair=controls[[s,t]].dropna();n=len(pair)
        continuity.append({'transition':s+' to '+t,'matched_controls':n,'complete_both':int((pair[s].eq(100)&pair[t].eq(100)).sum()),'percent':100*(pair[s].eq(100)&pair[t].eq(100)).mean() if n else np.nan})
    table(pd.DataFrame(continuity),'RQ2_T2','Same-control continuity only among explicitly matched reviewed controls')
    countries=sorted(latest.Country.unique());fig,ax=plt.subplots(figsize=(9,4))
    for i,c in enumerate(countries):
        vals=latest.loc[latest.Country.eq(c),'strict'];ax.scatter(i+np.linspace(-.1,.1,len(vals)),vals)
    ax.set_xticks(range(len(countries)),countries,rotation=35,ha='right');ax.set(ylabel='Reviewed strict chain rate %',ylim=(-3,103))
    figure(fig,latest[['canonical_id','Country','strict']],'RQ3_F1','Descriptive countries using latest reviewed corporate reports')
    periods=sorted(score['Reporting Period'].unique(),key=lambda s:(int(s.split()[1]),s.split()[0]));fig,ax=plt.subplots(figsize=(8,4))
    for i,t in enumerate(periods):
        vals=score.loc[score['Reporting Period'].eq(t),'strict'];ax.scatter(i+np.linspace(-.1,.1,len(vals)),vals)
    ax.set_xticks(range(len(periods)),periods,rotation=25);ax.set(ylabel='Reviewed strict chain rate %',ylim=(-3,103))
    figure(fig,score[['canonical_id','report_id','Reporting Period','strict']],'RQ3_F2','All reviewed reports by period; repeated firms and questionnaire changes remain confounders')
    table(score.groupby(['Country','Reporting Period','template_fingerprint']).size().rename('n_reports').reset_index(),'RQ3_T1','Country period and observed questionnaire composition')
    pairs=[]
    for firm,g in score.groupby('canonical_id'):
        g=g.sort_values(['date','report_id'])
        if len(g)<2:continue
        x,y=g.iloc[0],g.iloc[-1]
        old=u.loc[u.report_id.eq(x.report_id)].set_index(['control_id','stage']);new=u.loc[u.report_id.eq(y.report_id)].set_index(['control_id','stage']);common=old.index.intersection(new.index)
        pairs.append({'canonical_id':firm,'n_matched_control_stages':len(common),'change_pp':(new.loc[common,'strict'].mean()-old.loc[common,'strict'].mean()) if len(common) else np.nan,'same_question_set':x.template_fingerprint==y.template_fingerprint})
    pd.DataFrame(pairs,columns=['canonical_id','n_matched_control_stages','change_pp','same_question_set']).to_csv(out/'supplement_matched_control_changes.csv',index=False)
    adjusted,diagnostic=adjust_context(latest)
    table(adjusted,'RQ3_T2','Exploratory linear country contrasts adjusted for response length and questionnaire fingerprint; noncausal')
    (out/'context_model_diagnostics.json').write_text(json.dumps(diagnostic,indent=2))
    accuracy=pd.read_csv(evaluation_dir/'candidate_validation.csv')
    agreement=pd.read_csv(evaluation_dir/'intercoder_agreement.csv')
    fig,ax=plt.subplots(figsize=(9,4));x=np.arange(len(accuracy))
    for offset,col in [(-.22,'weighted_precision'),(0,'weighted_recall'),(.22,'weighted_f1')]:ax.bar(x+offset,accuracy[col],width=.22,label=col.replace('weighted_',''))
    ax.set_xticks(x,accuracy.dimension,rotation=20,ha='right');ax.set(ylim=(0,1.05),ylabel='Held-out weighted score');ax.legend()
    figure(fig,accuracy,'RQ4_F1','Automated rules versus adjudicated substantive evidence and complete chains')
    fig,ax=plt.subplots(figsize=(9,4));ax.bar(agreement.dimension,agreement.kappa);ax.tick_params(axis='x',rotation=35);ax.set(ylabel='Cohen kappa',ylim=(-1,1))
    figure(fig,agreement,'RQ4_F2','Independent held-out coding agreement; ordinal scores use quadratic weights')
    table(accuracy,'RQ4_T1','Weighted held-out precision recall F1 and company-bootstrap uncertainty')
    table(agreement,'RQ4_T2','Independent coding agreement with denominators; undefined kappa retained as missing')
    u.to_csv(out/'reviewed_unit_scores.csv',index=False);score.to_csv(out/'reviewed_report_scores.csv',index=False)
    require(len(registry)==16,'Expected sixteen result objects')
    manifest={'status':'reviewed disclosure analysis; does not verify internal effectiveness','outputs':registry,'input_hashes':{name:digest(w/name) for name in ['eligibility.csv','chain_units.csv','coverage.csv','frozen_sample.csv','coder_A.csv','coder_B.csv','adjudicated_sample.csv']}}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2));(out/'checksums.json').write_text(json.dumps({f.name:digest(f) for f in out.iterdir()},indent=2))
    print('Reviewed results:',shutil.make_archive(str(out),'zip',out))

# %% M6 Held-out evaluation never regenerates samples or silently drops annotation IDs

def evaluate(args):
    w=args.workspace;answers,reports,design=load_frozen(w);tables={}
    allowed=set(design.row_id)
    for label,filename in [('A','coder_A.csv'),('B','coder_B.csv'),('gold','adjudicated_sample.csv')]:
        frame=read(w/filename);check_ids(frame,'row_id',allowed,label)
        require(set(frame.row_id)==allowed,f'{label}: all frozen sampled answers must be assessed; no silent dropping')
        ratings(frame,COMP,[0,1,2,3]);ratings(frame,LINKS,[0,1]);tables[label]=frame
    held=set(design.loc[design.review_phase.eq('held_out'),'row_id']);require(len(held)>0,'Need held-out corporations')
    results=[]
    for c in COMP+LINKS:
        x=tables['A'].set_index('row_id').loc[sorted(held),c];y=tables['B'].set_index('row_id').loc[sorted(held),c]
        k=np.nan if len(set(x)|set(y))<2 else cohen_kappa_score(x,y,labels=[0,1,2,3] if c in COMP else [0,1],weights='quadratic' if c in COMP else None)
        results.append({'dimension':c,'n':len(x),'raw_agreement':float(x.eq(y).mean()),'kappa':k})
    gold=tables['gold'].set_index('row_id').loc[sorted(held)].copy()
    require(gold.adjudication_note.ne('').all(),'Record adjudication rationale')
    gold['complete']=gold[COMP].ge(2).all(axis=1)&gold[LINKS].eq(1).all(axis=1)
    source=answers.set_index('row_id')
    for rid,row in gold.loc[gold.complete].iterrows():require(bool(row.supporting_quote) and row.supporting_quote in source.loc[rid,'answer'],'Positive chain gold needs a verbatim source quote')
    d=design.set_index('row_id').loc[gold.index];weights=pd.to_numeric(d.sample_weight)
    targets={c:(gold[c].ge(2),d['candidate_'+c].str.lower().eq('true')) for c in COMP}
    targets['complete_chain']=(gold.complete,d.all_four_answer.str.lower().eq('true'))
    output=[];errors=[]
    for dimension,(truth,pred) in targets.items():
        pr,rc,f1,_=precision_recall_fscore_support(truth,pred,average='binary',sample_weight=weights,zero_division=0)
        intervals=cluster_intervals(truth.to_numpy(),pred.to_numpy(),weights.to_numpy(),d.canonical_id.to_numpy())
        output.append({'dimension':dimension,'held_out_n':len(gold),'gold_positive_n':int(truth.sum()),'weighted_precision':pr,'weighted_recall':rc,'weighted_f1':f1,**intervals})
        for rid in truth.index[truth.ne(pred)]:errors.append({'row_id':rid,'dimension':dimension,'gold':int(truth.loc[rid]),'prediction':int(pred.loc[rid]),'answer':source.loc[rid,'answer'],'review_note':gold.loc[rid,'review_note']})
    out=w/('evaluation_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir()
    pd.DataFrame(results).to_csv(out/'intercoder_agreement.csv',index=False)
    pd.DataFrame(output).to_csv(out/'candidate_validation.csv',index=False)
    pd.DataFrame(errors,columns=['row_id','dimension','gold','prediction','answer','review_note']).to_csv(out/'misclassification_audit.csv',index=False)
    (out/'inputs.json').write_text(json.dumps({n:digest(w/n) for n in ['coder_A.csv','coder_B.csv','adjudicated_sample.csv','frozen_sample.csv']},indent=2));print('Evaluation:',out)
    return out

# %% RQ3 context adjustment and RQ4 uncertainty

def adjust_context(frame):
    """Descriptive OLS contrasts with HC3 uncertainty; require an estimable design."""
    import statsmodels.api as sm
    design=pd.get_dummies(frame[['Country','template_fingerprint']],drop_first=True,dtype=float)
    design['log_answer_words']=np.log1p(pd.to_numeric(frame.answer_words))
    X=sm.add_constant(design,has_constant='add').astype(float);n,p=X.shape
    rank=int(np.linalg.matrix_rank(X.to_numpy()))
    diagnostics={'n_companies':n,'n_parameters':p,'matrix_rank':rank,'status':'not_estimable','interpretation':'descriptive association, not causal; one latest report per canonical company'}
    if n<=p+2 or rank<p:
        return pd.DataFrame([{'term':'not estimable','reason':'Insufficient residual degrees of freedom or confounded country/template design'}]),diagnostics
    fit=sm.OLS(frame.strict.astype(float),X).fit(cov_type='HC3')
    ci=fit.conf_int();diagnostics.update(status='estimated',r_squared=float(fit.rsquared))
    return pd.DataFrame({'term':X.columns,'coefficient_pp':fit.params.values,'hc3_se':fit.bse.values,'lower_95':ci[0].values,'upper_95':ci[1].values}),diagnostics

def cluster_intervals(truth,pred,weights,company,repetitions=500):
    """Resample held-out companies; use fixed design weights within each draw.
    Percentile intervals are descriptive for this selected validation sample.
    Degenerate single-class precision/recall draws are omitted rather than scored zero.
    """
    ids=np.unique(company);result={}
    if len(ids)<5:
        return {k:np.nan for k in ['precision_low','precision_high','recall_low','recall_high','f1_low','f1_high']}
    rng=np.random.default_rng(42);draws=[]
    for _ in range(repetitions):
        indices=np.concatenate([np.flatnonzero(company==c) for c in rng.choice(ids,size=len(ids),replace=True)])
        if not truth[indices].any() or not pred[indices].any():continue
        draws.append(precision_recall_fscore_support(truth[indices],pred[indices],average='binary',sample_weight=weights[indices],zero_division=0)[:3])
    for j,name in enumerate(['precision','recall','f1']):
        result[name+'_low'],result[name+'_high']=np.percentile(np.array(draws)[:,j],[2.5,97.5]) if len(draws)>=100 else (np.nan,np.nan)
    return result

def status(args):
    w=args.workspace
    print('WORKSPACE:',w)
    for name,columns in [('eligibility.csv',['canonical_id','corporate_eligible','reviewed','identity_source','decision_note']),('chain_units.csv',COMP+LINKS+['reviewed']),('coverage.csv',['applicable','review_complete','review_scope','rationale']),('coder_A.csv',COMP+LINKS),('coder_B.csv',COMP+LINKS),('adjudicated_sample.csv',COMP+LINKS+['adjudication_note'])]:
        path=w/name
        if not path.exists():print(name,': not created yet');continue
        f=read(path);blank=sum(int(f[c].eq('').sum()) if c in f else len(f) for c in columns)
        print(name,':',len(f),'rows;',blank,'blank required cells')
    print('NEXT: complete eligibility then freeze; independently code and adjudicate; complete chain units/coverage; analyse.')

# %% Command-line workflow

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage',choices=['prepare','freeze','analyse','evaluate','status'],nargs='?',default='prepare')
    parser.add_argument('--data',type=Path,default=BASE/'transparency-reports-exports.csv')
    parser.add_argument('--workspace',type=Path,default=BASE/'study_aligned')
    args=parser.parse_args();args.workspace=args.workspace.resolve();args.data=args.data.resolve()
    try:{'prepare':prepare,'freeze':freeze,'analyse':analyse,'evaluate':evaluate,'status':status}[args.stage](args)
    except (ValueError,FileNotFoundError,KeyError) as exc:parser.exit(2,'Study incomplete or invalid: '+str(exc)+'\n')
if __name__=='__main__':main()
