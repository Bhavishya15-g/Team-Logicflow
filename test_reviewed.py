"""Synthetic fixtures validate software only; they are never research data or findings."""
import unittest,tempfile,json,hashlib
from pathlib import Path
from types import SimpleNamespace
import pandas as pd
import implementation as m
class Tests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.w=Path(self.temp.name);reports=[];rows=[];e=[]
  self.quote='The board reviews audit reports and orders corrective action.'
  for i in range(4):
   firm=f'Company{i}';rid=f'report{i}'
   reports.append({'report_id':rid,'Organization':firm,'Country':'Country'+str(i%2),'Reporting Period':'Q2 2026','Publication Date':'June 1, 2026','date':'2026-06-01','template_fingerprint':'template'})
   rows.append({'row_id':f'answer{i}','report_id':rid,'Organization':firm,'Country':'Country'+str(i%2),'question':'Governance question','answer':self.quote,'eligible':'True','all_four_answer':str(i%2==0),**{'original_'+c:str(i%2==0) for c in m.COMP}})
   e.append({'Organization':firm,'Country':'Country'+str(i%2),'canonical_id':f'company{i}','corporate_eligible':'1','reviewed':'1','identity_source':'fixture only','decision_note':'fixture only'})
  pd.DataFrame(reports).to_csv(self.w/'report_inventory.csv',index=False);pd.DataFrame(rows).to_csv(self.w/'answer_features_and_audit.csv',index=False);pd.DataFrame(e).to_csv(self.w/'eligibility.csv',index=False)
  (self.w/'lexicon_and_stage_rules.json').write_text('{}');self.data=self.w/'input.csv';self.data.write_text('fixture only')
  (self.w/'study.json').write_text(json.dumps({'input_sha256':m.digest(self.data),'corpus_sha256':m.digest(self.w/'answer_features_and_audit.csv'),'reports_sha256':m.digest(self.w/'report_inventory.csv')}))
  self.args=SimpleNamespace(workspace=self.w,data=self.data);m.freeze(self.args)
 def tearDown(self):self.temp.cleanup()
 def annotate(self):
  r=m.read(self.w/'eligible_reports.csv');a=m.read(self.w/'eligible_answers.csv');rows=[]
  for _,report in r.iterrows():
   rid=report.report_id;row_id=a.loc[a.report_id.eq(rid),'row_id'].iloc[0]
   for stage in m.STAGES:
    row={'unit_id':rid+stage,'report_id':rid,'control_id':'control1','stage':stage,'row_ids':row_id,'quote':self.quote,'link_quote':self.quote,'artifact_access':'internal','artifact_url':'','reviewed':'1','review_note':'fixture only'}
    row.update({c:2 for c in m.COMP});row.update({c:1 for c in m.LINKS});rows.append(row)
  pd.DataFrame(rows).to_csv(self.w/'chain_units.csv',index=False)
  cv=m.read(self.w/'coverage.csv');cv['applicable']='1';cv['review_complete']='1';cv['review_scope']='All fixture answers';cv['rationale']='fixture';cv.to_csv(self.w/'coverage.csv',index=False)
  p=m.read(self.w/'principles.csv');p['present']='1';p['row_id']=p.report_id.map(a.set_index('report_id').row_id);p['quote']=self.quote;p['reviewed']='1';p['rationale']='fixture only';p.to_csv(self.w/'principles.csv',index=False)
 def test_unknown_ids_rejected(self):
  with self.assertRaises(ValueError):m.check_ids(pd.DataFrame({'row_id':['unknown']}),'row_id',{'known'},'test')
 def test_freeze_never_redraws(self):
  original=m.digest(self.w/'frozen_sample.csv')
  with self.assertRaises(ValueError):m.freeze(self.args)
  self.assertEqual(original,m.digest(self.w/'frozen_sample.csv'))
 def test_eligibility_change_blocks_analysis(self):
  with (self.w/'eligibility.csv').open('a') as f:f.write('\n')
  with self.assertRaises(ValueError):m.load_frozen(self.w)
 def test_empty_human_codes_block_findings(self):
  with self.assertRaises(ValueError):m.validate_units(self.w)
 def test_reviewed_units_and_16_exports(self):
  self.annotate();m.validate_units(self.w);self.fill_raters();m.analyse(self.args)
  out=next(p for p in self.w.glob('reviewed_results_*') if p.is_dir());reg=json.loads((out/'manifest.json').read_text())['outputs'];self.assertEqual(len(reg),16)
  for rec in reg:self.assertGreater((out/(rec['id']+'.pdf')).stat().st_size,100)
 def test_invalid_quote_blocks_analysis(self):
  self.annotate();u=m.read(self.w/'chain_units.csv');u.loc[0,'quote']='fabricated quotation';u.to_csv(self.w/'chain_units.csv',index=False)
  with self.assertRaises(ValueError):m.validate_units(self.w)
 def test_unknown_gold_ids_not_silently_dropped(self):
  for name in ['coder_A.csv','coder_B.csv','adjudicated_sample.csv']:
   f=m.read(self.w/name);f.loc[0,'row_id']='unknown';f.to_csv(self.w/name,index=False)
  with self.assertRaises(ValueError):m.evaluate(self.args)
 def fill_raters(self):
  for name in ['coder_A.csv','coder_B.csv','adjudicated_sample.csv']:
   f=m.read(self.w/name)
   for c in m.COMP:f[c]=2
   for c in m.LINKS:f[c]=1
   f['supporting_quote']=self.quote;f['adjudication_note']='fixture adjudication';f.to_csv(self.w/name,index=False)
 def test_heldout_evaluation_from_completed_fixtures(self):
  self.fill_raters();out=m.evaluate(self.args)
  self.assertEqual(len(pd.read_csv(out/'candidate_validation.csv')),5)
 def test_invalid_scale_rejected(self):
  self.annotate();u=m.read(self.w/'chain_units.csv');u.loc[0,m.COMP[0]]=4;u.to_csv(self.w/'chain_units.csv',index=False)
  with self.assertRaises(ValueError):m.validate_units(self.w)
 def test_score_three_needs_traceability(self):
  self.annotate();u=m.read(self.w/'chain_units.csv');u.loc[0,m.COMP[0]]=3;u.to_csv(self.w/'chain_units.csv',index=False)
  with self.assertRaises(ValueError):m.validate_units(self.w)
 def test_bootstrap_small_sample_is_not_fabricated(self):
  import numpy as np
  result=m.cluster_intervals(np.array([True]),np.array([True]),np.array([1]),np.array(['one']))
  self.assertTrue(all(np.isnan(v) for v in result.values()))
 def test_estimable_context_adjustment(self):
  import numpy as np
  rng=np.random.default_rng(10);n=60
  frame=pd.DataFrame({'Country':['A','B']*30,'template_fingerprint':['x','x','y','y']*15,'answer_words':rng.integers(50,2000,n)})
  frame['strict']=10+2*np.log1p(frame.answer_words)+rng.normal(0,1,n)
  coef,info=m.adjust_context(frame)
  self.assertEqual(info['status'],'estimated');self.assertIn('log_answer_words',set(coef.term))
 def test_bootstrap_with_enough_companies(self):
  import numpy as np
  result=m.cluster_intervals(np.array([True,False]*6),np.array([True,True]*6),np.ones(12),np.repeat(np.arange(6),2))
  self.assertTrue(all(np.isfinite(v) for v in result.values()))
if __name__=='__main__':unittest.main(verbosity=2)
