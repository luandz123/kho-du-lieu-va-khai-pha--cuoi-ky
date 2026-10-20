"""Create S11B-3 once using supported REST API; never recreate an existing dashboard."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'dashboard/overview'))
from superset_api import SupersetAPI
D=ROOT/'dashboard/preferences'
def write(name,obj):
 (D/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def metric(expression,label):
 return dict(expressionType='SQL',sqlExpression=expression,label=label,hasCustomLabel=True,optionName='metric_'+label)
def main():
 assert not (D/'object_ids.json').exists(),'INSPECT_EXISTING_OBJECTS_DO_NOT_RECREATE'
 api=SupersetAPI();ids={'database':1,'charts':{}};defs={}
 for key in ['users','profile']:
  r=api.request('POST','/api/v1/dataset/',dict(database=1,schema='analytics',table_name='P1_11B_'+key,sql=(D/(key+'_dataset.sql')).read_text(encoding='utf-8'),owners=[1]));ids[key]=r['id'];write('object_ids.json',ids)
  api.request('PUT',f'/api/v1/dataset/{r["id"]}',{'description':'S11B active+valid only. '+('One user per row; fixed window denominators before native filters; includes insufficient cluster NULL.' if key=='users' else 'One cluster x genre; precomputed preference. EXCLUDE age/gender filters; never SUM repeated n_users.')})
 assigned=metric("COUNT(*) FILTER (WHERE status='assigned')",'assigned_users')
 insufficient=metric("COUNT(*) FILTER (WHERE status='insufficient_evidence')",'insufficient_users')
 baseline=metric('MAX(assigned_total)','fixed_assigned_baseline')
 share=metric("100.0*COUNT(*) FILTER (WHERE status='assigned')/NULLIF(MAX(assigned_total),0)",'pct_of_fixed_6038')
 cluster_n=metric('MAX(original_cluster_n)','original_cluster_users')
 cluster_pct=metric("100.0*COUNT(*) FILTER (WHERE status='assigned')/NULLIF(MAX(original_cluster_n),0)",'pct_of_original_cluster')
 specs=[
  ('assigned','User assigned · chịu 3 filter','users','big_number_total',[],[assigned]),
  ('insufficient','Thiếu bằng chứng · cố định toàn mô hình','users','big_number_total',[],[insufficient]),
  ('baseline','Baseline assigned · cố định 6.038','users','big_number_total',[],[baseline]),
  ('size','Quy mô cụm · % trên 6.038 assigned gốc','users','table',['cluster_label'],[assigned,share]),
  ('model','Phiên bản active + valid · toàn mô hình','users','table',['model_version'],[assigned,insufficient]),
  ('heatmap','Profile cụm × genre · không lọc tuổi/giới','profile','heatmap_v2',['genre_name','cluster_label'],[metric('MAX(mean_preference)','mean_preference')]),
  ('gender','Giới tính theo cụm · so baseline cố định','users','table',['cluster_label','gender'],[assigned,cluster_n,cluster_pct,metric('MAX(baseline_gender_n)','baseline_gender_users'),metric('100.0*MAX(baseline_gender_n)/MAX(assigned_total)','baseline_gender_pct')]),
  ('baseline_gender','Giới tính baseline · toàn bộ assigned','users','echarts_timeseries_bar',['gender'],[assigned]),
  ('age','Nhóm tuổi theo cụm · so baseline cố định','users','table',['cluster_label','age_group'],[assigned,cluster_n,cluster_pct,metric('MAX(baseline_age_n)','baseline_age_users'),metric('100.0*MAX(baseline_age_n)/MAX(assigned_total)','baseline_age_pct')]),
  ('baseline_age','Tuổi baseline · toàn bộ assigned','users','echarts_timeseries_bar',['age_group'],[assigned])]
 for key,title,dskey,viz,cols,metrics in specs:
  ds=ids[dskey];where="status='assigned'" if key in ['size','gender','age','baseline_gender','baseline_age'] else ''
  adhoc=[] if not where else [{'expressionType':'SQL','sqlExpression':where,'clause':'WHERE','filterOptionName':'assigned_only'}]
  p=dict(datasource=f'{ds}__table',viz_type=viz,adhoc_filters=adhoc,time_range='No filter',granularity_sqla=None,row_limit=1000,color_scheme='supersetColors')
  q=dict(columns=cols,metrics=metrics,orderby=[[x,True] for x in cols],row_limit=1000,granularity=None,time_range='No filter',is_timeseries=False,extras={'where':where,'having':''})
  if viz=='big_number_total':
   p.update(metric=metrics[0],y_axis_format=',d',header_font_size=.38,subheader={'assigned':'User có cụm trong bộ lọc hiện tại','insufficient':'Không có đánh giá tích cực đủ làm vector; cluster NULL','baseline':'Mẫu số cố định, không chịu cluster / tuổi / giới'}[key])
  elif viz=='table':
   sort=metric('ROW('+','.join('MIN('+x+')' for x in cols)+')','row_order')
   p.update(query_mode='aggregate',groupby=cols,all_columns=[],metrics=metrics,percent_metrics=[],timeseries_limit_metric=sort,order_desc=False,page_length=30,server_pagination=False,include_search=False,show_cell_bars=False,column_config={m['label']:{'d3NumberFormat':'.2f' if 'pct' in m['label'] else ',d'} for m in metrics})
   q['orderby']=[[sort,True]]
  elif viz=='heatmap_v2':
   p.update(x_axis='genre_name',groupby=['cluster_label'],metric=metrics[0],sort_x_axis='alpha_asc',sort_y_axis='alpha_asc',normalize_across='heatmap',normalized=False,show_percentage=False,show_values=False,show_legend=True,legend_type='continuous',linear_color_scheme='blue_white_yellow',y_axis_format='.2%',value_bounds=[0,.4],xAxisLabelRotation=45,left_margin=230,bottom_margin=100,xscale_interval=1,yscale_interval=1)
  else:
   p.update(x_axis=cols[0],metrics=metrics,groupby=[],orientation='vertical',show_value=True,show_legend=False,x_axis_sort=cols[0],x_axis_sort_asc=True,order_desc=False,rich_tooltip=True,y_axis_format=',d')
  ctx=dict(datasource={'id':ds,'type':'table'},force=False,queries=[q],form_data=p,result_format='json',result_type='full')
  r=api.request('POST','/api/v1/chart/',dict(slice_name='P1 11B · '+title,description='Historical positive-rating preferences; no causal demographic inference. Denominators and scope shown on dashboard.',viz_type=viz,datasource_id=ds,datasource_type='table',owners=[1],params=json.dumps(p),query_context=json.dumps(ctx)))
  ids['charts'][key]=r['id'];defs[key]={'chart_id':r['id'],'form_data':p,'query_context':ctx};write('object_ids.json',ids);write('chart_definitions.json',defs)
 note='''### Sở thích trong lịch sử đánh giá · kmeans_k4_seed42
**6.038 assigned + 2 thiếu bằng chứng = 6.040 user.** Thiếu bằng chứng: không có đánh giá tích cực (rating ≥4) để tạo vector, cluster NULL; KPI này và baseline cố định không chịu filter.
**Filter Cụm / Tuổi / Giới:** chỉ lọc KPI assigned, quy mô và bảng nhân khẩu học. Heatmap chỉ chịu **Cụm**; không chịu Tuổi/Giới vì profile đã tính sẵn trên toàn cụm, không được tái tính theo người đang lọc. Bỏ chọn = toàn bộ.
**Mẫu số:** quy mô % dùng **6.038 assigned gốc**. Bảng nhân khẩu học: % cụm = số user đang chọn / **quy mô gốc cụm**; % baseline = số user thuộc nhóm tuổi/giới trong toàn bộ assigned / **6.038**, luôn cố định. Khi lọc nhân khẩu học, các tỷ trọng cụm không chuẩn hóa lại về 100%. Hai biểu đồ baseline luôn giữ toàn bộ assigned.
Heatmap = **mean_preference** P2 bàn giao, trung bình tỷ lệ genre từ đánh giá tích cực; tổng 18 giá trị mỗi cụm =1. Màu dùng thang cố định 0–40%; không cộng n_users lặp trên 18 genre. Không join profile vào user để đếm người.
Tên cụm mô tả theo báo cáo Q1 P2: 0 đa dạng/cân bằng; 1 Drama/tình cảm; 2 Comedy; 3 Action/Sci-Fi/Thriller. Tuổi/giới chỉ mô tả cơ cấu lịch sử, không tham gia huấn luyện và không chứng minh nguyên nhân hay thay đổi sở thích cùng một người theo tuổi. Rating là **đánh giá**, không phải lượt xem hoặc nhu cầu hiện tại.'''
 rows=[('R1',['assigned','insufficient','baseline']),('R2',['size','model']),('R3',['heatmap']),('R4',['gender','baseline_gender']),('R5',['age','baseline_age'])]
 pos={'DASHBOARD_VERSION_KEY':'v2','ROOT_ID':{'id':'ROOT_ID','type':'ROOT','children':['GRID_ID']},'GRID_ID':{'id':'GRID_ID','type':'GRID','parents':['ROOT_ID'],'children':['NOTE']+[r for r,_ in rows]},'NOTE':{'id':'NOTE','type':'MARKDOWN','parents':['ROOT_ID','GRID_ID'],'children':[],'meta':{'width':12,'height':45,'code':note,'background':'BACKGROUND_TRANSPARENT'}}}
 for row,keys in rows:
  pos[row]={'id':row,'type':'ROW','parents':['ROOT_ID','GRID_ID'],'children':[],'meta':{'background':'BACKGROUND_TRANSPARENT'}}
  for i,key in enumerate(keys):
   node='CHART-'+key;pos[row]['children'].append(node)
   widths=[8,4] if row in ['R4','R5'] else [12//len(keys)]*len(keys)
   pos[node]={'id':node,'type':'CHART','parents':['ROOT_ID','GRID_ID',row],'children':[],'meta':{'chartId':ids['charts'][key],'width':widths[i],'height':26 if row=='R1' else (85 if row=='R5' else (32 if row=='R2' else 55)),'sliceName':key}}
 common=dict(filterType='filter_select',type='NATIVE_FILTER',controlValues={'enableEmptyFilter':False,'defaultToFirstItem':False,'multiSelect':True,'searchAllOptions':False,'inverseSelection':False},cascadeParentIds=[],defaultDataMask={'extraFormData':{},'filterState':{}})
 filters=[]
 for key,name,col,ds in [('cluster','Cụm · không lọc baseline / thiếu bằng chứng','cluster_id',ids['profile']),('age','Nhóm tuổi · không lọc heatmap','age_group',ids['users']),('gender','Giới tính · không lọc heatmap','gender',ids['users'])]:
  excluded=['insufficient','baseline','model','baseline_gender','baseline_age']+([] if key=='cluster' else ['heatmap'])
  filters.append(dict(common,id='NATIVE_FILTER-11B-'+key.upper(),name=name,description='Baseline cố định toàn bộ 6.038 assigned. Profile không tái tính theo tuổi/giới.',targets=[{'datasetId':ds,'column':{'name':col}}],scope={'rootPath':['ROOT_ID'],'excluded':[ids['charts'][k] for k in excluded]}))
 meta={'native_filter_configuration':filters,'refresh_frequency':0,'expanded_slices':{},'color_scheme':'supersetColors','chart_configuration':{},'shared_label_colors':{},'timed_refresh_immune_slices':[]}
 dash=dict(dashboard_title='MovieLens 1M · Sở thích và cơ cấu cụm',slug='movielens-preferences',owners=[1],published=True,position_json=json.dumps(pos,ensure_ascii=False),json_metadata=json.dumps(meta,ensure_ascii=False))
 r=api.request('POST','/api/v1/dashboard/',dash);ids['dashboard']=r['id'];write('object_ids.json',ids);write('dashboard_definition.json',dash)
 for cid in ids['charts'].values():api.request('PUT',f'/api/v1/chart/{cid}',{'dashboards':[ids['dashboard']]})
 print(json.dumps({'status':'CREATED','ids':ids,'url':api.base+f'/superset/dashboard/{ids["dashboard"]}/'}))
if __name__=='__main__':main()
