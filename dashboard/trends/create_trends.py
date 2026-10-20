"""Create only S11C through supported Superset REST endpoints, no metadata SQL.

Rerun guard: inspect saved IDs and actual objects before changing existing objects.
"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'dashboard/overview'))
from superset_api import SupersetAPI
D=ROOT/'dashboard/trends'
def write(name,obj):
 (D/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def metric(col,label=None,agg='MAX'):
 return {'expressionType':'SQL','sqlExpression':f'{agg}({col})','label':label or col,'hasCustomLabel':True,'optionName':'metric_'+(label or col)}
def main():
 if (D/'object_ids.json').exists():raise RuntimeError('INSPECT_EXISTING_OBJECTS_DO_NOT_RECREATE')
 api=SupersetAPI();ids={'database':1,'charts':{}};defs={}
 for key in ['quarter','genre']:
  r=api.request('POST','/api/v1/dataset/',{'database':1,'schema':'analytics','table_name':'P1_11C_'+key,'sql':(D/(key+'_dataset.sql')).read_text(encoding='utf-8'),'owners':[1]})
  ids[key]=r['id'];write('object_ids.json',ids)
  api.request('PUT',f'/api/v1/dataset/{r["id"]}',{'description':'S11C; complete UTC quarters. Native categorical quarter selector filters display rows AFTER approved O4/O5 calculations. Genre share denominator always all18 genres. No demographic slicing.'})
 specs=[('system','Đánh giá duy nhất theo quý · không chịu filter genre','quarter','rating_count'),
        ('genre_count','Lượt gắn genre theo quý · không cộng thành tổng hệ thống','genre','rating_count'),
        ('qoq','QoQ genre (%) · âm là giảm; NULL xem bảng chi tiết','genre','qoq_pct'),
        ('share','Tỷ trọng genre (%) · mẫu số toàn bộ 18 genre','genre','genre_share_pct'),
        ('detail','Đối soát quý × genre · N/A, quý biên và hạng toàn bộ genre','genre',None)]
 for key,title,dskey,col in specs:
  ds=ids[dskey];cols=['quarter_label']+([] if dskey=='quarter' else ['genre_name'])
  metrics=[metric(col)] if col else [metric(x) for x in ['rating_count','previous_rating_count','genre_assignment_total','genre_share_pct','qoq_pct','growth_rank']]
  if key=='detail':cols+=['ranking_status','rank_interpretation']
  p={'datasource':f'{ds}__table','viz_type':'echarts_timeseries_bar','adhoc_filters':[],'time_range':'No filter','granularity_sqla':None,'x_axis':'quarter_label','metrics':metrics,'groupby':([] if dskey=='quarter' else ['genre_name']),'orientation':'vertical','show_value':dskey=='quarter','show_legend':dskey!='quarter','legendType':'scroll','legendOrientation':'top','x_axis_sort':'quarter_label','x_axis_sort_asc':True,'order_desc':False,'rich_tooltip':True,'y_axis_format':',d' if col=='rating_count' else '.2f','x_axis_title':'Quý UTC (chọn trọn quý)','y_axis_title':'Đánh giá duy nhất' if key=='system' else ('Lượt gắn genre' if key=='genre_count' else '%'),'color_scheme':'supersetColors','row_limit':1000,'truncateXAxis':False,'xAxisLabelRotation':45,'show_empty_columns':True,'contributionMode':None}
  q={'columns':cols,'metrics':metrics,'orderby':[['quarter_label',True]]+([] if dskey=='quarter' else [['genre_name',True]]),'row_limit':1000,'granularity':None,'time_range':'No filter','is_timeseries':False,'extras':{'where':'','having':''}}
  if key=='detail':
   sort_metric=metric('quarter_start','quarter_genre_order');sort_metric['sqlExpression']='ROW(MIN(quarter_start),MIN(genre_name))'
   p.update(viz_type='table',query_mode='aggregate',groupby=cols,all_columns=[],percent_metrics=[],timeseries_limit_metric=sort_metric,order_desc=False,page_length=15,server_pagination=False,include_search=True,show_cell_bars=False,column_config={x:{'d3NumberFormat':'.2f'} for x in ['qoq_pct','genre_share_pct']},table_timestamp_format='smart_date')
   p['column_config'].update({x:{'d3NumberFormat':',d'} for x in ['rating_count','previous_rating_count','genre_assignment_total','growth_rank']})
   q['orderby']=[[p['timeseries_limit_metric'],True]]
  ctx={'datasource':{'id':ds,'type':'table'},'force':False,'queries':[q],'form_data':p,'result_format':'json','result_type':'full'}
  r=api.request('POST','/api/v1/chart/',{'slice_name':'P1 11C · '+title,'description':'One full UTC quarter'+(' x genre; precomputed QoQ/share/global rank before display filters. NULL means unavailable. No age/gender filter.' if dskey=='genre' else '; O4 quarter rows only. Genre filter excluded.'),'viz_type':p['viz_type'],'datasource_id':ds,'datasource_type':'table','owners':[1],'params':json.dumps(p),'query_context':json.dumps(ctx)})
  ids['charts'][key]=r['id'];defs[key]={'chart_id':r['id'],'form_data':p,'query_context':ctx};write('object_ids.json',ids);write('chart_definitions.json',defs)
 note='''### Xu hướng đánh giá lịch sử · UTC
**Chọn quý nguyên vẹn** ở bộ lọc Quý hiển thị (có thể chọn nhiều quý liên tiếp); bỏ chọn = toàn bộ. Không diễn giải khoảng ngày lẻ như một quý đầy đủ.
**Genre chỉ lọc 4 biểu đồ/bảng genre**, không lọc biểu đồ đánh giá duy nhất toàn hệ thống. Tỷ trọng dùng tổng lượt gắn **toàn bộ 18 genre trong cùng quý**, kể cả khi chỉ chọn 1 genre. Không cộng số genre thành rating duy nhất.
QoQ và hạng tính trên chuỗi đầy đủ **trước khi lọc quý/genre**; zero-fill trước LAG; quý trước 0/chưa có ⇒ NULL (N/A). Xếp hạng toàn bộ genre chỉ khi quý trước ≥100 và cả hai quý không biên. Hạng 1 có QoQ âm = **giảm ít nhất**, không phải tăng dương.
**2000 Q2 và 2003 Q1 là quý biên thiếu quan sát**; 2000 Q3 có quý trước là biên nên không xếp hạng. NULL trong bảng là không có giá trị, không phải 0. Mức QoQ/tỷ trọng là %, không cộng % giữa các quý.
Nguồn 25/04/2000–28/02/2003; rating là đánh giá, không phải lượt xem/doanh thu/nhu cầu hiện tại. Không lọc tuổi/giới vì O5 đã tổng hợp toàn bộ nhân khẩu học.'''
 pos={'DASHBOARD_VERSION_KEY':'v2','ROOT_ID':{'id':'ROOT_ID','type':'ROOT','children':['GRID_ID']},'GRID_ID':{'id':'GRID_ID','type':'GRID','parents':['ROOT_ID'],'children':['NOTE','ROW1','ROW2','ROW3','ROW4']},'NOTE':{'id':'NOTE','type':'MARKDOWN','parents':['ROOT_ID','GRID_ID'],'children':[],'meta':{'width':12,'height':38,'code':note,'background':'BACKGROUND_TRANSPARENT'}}}
 for row,keys in [('ROW1',['system']),('ROW2',['genre_count','share']),('ROW3',['qoq']),('ROW4',['detail'])]:
  pos[row]={'id':row,'type':'ROW','parents':['ROOT_ID','GRID_ID'],'children':[],'meta':{'background':'BACKGROUND_TRANSPARENT'}}
  for key in keys:
   node='CHART-'+key;pos[row]['children'].append(node);pos[node]={'id':node,'type':'CHART','parents':['ROOT_ID','GRID_ID',row],'children':[],'meta':{'chartId':ids['charts'][key],'width':12//len(keys),'height':75 if key=='detail' else 48,'sliceName':key}}
 common={'filterType':'filter_select','type':'NATIVE_FILTER','controlValues':{'enableEmptyFilter':False,'defaultToFirstItem':False,'multiSelect':True,'searchAllOptions':False,'inverseSelection':False},'cascadeParentIds':[],'defaultDataMask':{'extraFormData':{},'filterState':{}},'scope':{'rootPath':['ROOT_ID'],'excluded':[]}}
 filters=[dict(common,id='NATIVE_FILTER-11C-QUARTER',name='Quý hiển thị (UTC) · chọn trọn quý',description='Chọn các quý liên tiếp; bỏ chọn = toàn bộ. Lọc sau QoQ/rank; không dùng khoảng ngày lẻ.',targets=[{'datasetId':ids['genre'],'column':{'name':'quarter_label'}}]),dict(common,id='NATIVE_FILTER-11C-GENRE',name='Genre · chỉ biểu đồ genre',description='Không lọc tổng hệ thống. Mẫu số tỷ trọng giữ toàn bộ 18 genre.',targets=[{'datasetId':ids['genre'],'column':{'name':'genre_name'}}],scope={'rootPath':['ROOT_ID'],'excluded':[ids['charts']['system']]})]
 meta={'native_filter_configuration':filters,'refresh_frequency':0,'expanded_slices':{},'color_scheme':'supersetColors','chart_configuration':{},'shared_label_colors':{},'timed_refresh_immune_slices':[]}
 dash={'dashboard_title':'MovieLens 1M · Xu hướng đánh giá theo quý','slug':'movielens-trends','owners':[1],'published':True,'position_json':json.dumps(pos,ensure_ascii=False),'json_metadata':json.dumps(meta,ensure_ascii=False)}
 r=api.request('POST','/api/v1/dashboard/',dash);ids['dashboard']=r['id'];write('object_ids.json',ids);write('dashboard_definition.json',dash)
 for cid in ids['charts'].values():api.request('PUT',f'/api/v1/chart/{cid}',{'dashboards':[ids['dashboard']]})
 print(json.dumps({'status':'CREATED','ids':ids,'url':api.base+f'/superset/dashboard/{ids["dashboard"]}/'}))
if __name__=='__main__':main()
