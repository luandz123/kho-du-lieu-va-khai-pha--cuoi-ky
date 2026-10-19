"""Create only P1 S11A objects through the official Superset API."""
import json
from pathlib import Path
from superset_api import SupersetAPI,ROOT
D=ROOT/'dashboard/overview'
def main():
 s=SupersetAPI();ids=json.loads((D/'object_ids.json').read_text(encoding='utf-8'));m=json.loads((D/'metrics.json').read_text(encoding='utf-8'))
 if 'dashboard' in ids:raise RuntimeError('OBJECTS_ALREADY_CREATED_INSPECT_BEFORE_REBUILD')
 specs=[('ratings','Tổng số đánh giá','rating_count',',d'),('mean','Điểm trung bình · SUM/COUNT','weighted_mean','.4f'),('users','User có đánh giá','rated_users',',d'),('movies','Phim có đánh giá','rated_movies',',d'),('catalog','Phim danh mục · cố định mọi thời kỳ','catalog_movies',',d'),('sum','Tổng điểm đánh giá','rating_sum',',d')]
 configs={};ids['charts']={}
 for key,title,metric,fmt in specs+[('top10','Top 10 phim · số đánh giá, điểm TB, ID','rating_count',',d'),('stars','Phân bố số đánh giá theo mức sao','rating_count',',d')]:
  ds=ids['catalog'] if key=='catalog' else ids['ratings']
  p={'datasource':str(ds)+'__table','viz_type':'big_number_total','metric':m[metric],'adhoc_filters':[],'time_range':'No filter','granularity_sqla':None if key=='catalog' else 'rated_at_utc','y_axis_format':fmt,'header_font_size':0.38,'subheader_font_size':0.12,'subheader':'Không chịu bộ lọc thời gian' if key=='catalog' else 'Thời điểm đánh giá UTC','force_timestamp_formatting':False,'row_limit':10000}
  q={'columns':[],'metrics':[m[metric]],'orderby':[],'row_limit':1,'granularity':p['granularity_sqla'],'time_range':'No filter','is_timeseries':False,'extras':{'where':'','having':''}}
  if key=='top10':
   p.update(viz_type='table',query_mode='aggregate',groupby=['movie_id','title'],metrics=[m['rating_count'],m['weighted_mean']],all_columns=[],percent_metrics=[],timeseries_limit_metric=m['top10_sort_row'],order_desc=True,row_limit=10,server_pagination=False,page_length=10,include_search=False,show_cell_bars=False,column_config={'weighted_mean':{'d3NumberFormat':'.4f'},'rating_count':{'d3NumberFormat':',d'},'movie_id':{'d3NumberFormat':'d'}},table_timestamp_format='smart_date')
   q.update(columns=['movie_id','title'],metrics=[m['rating_count'],m['weighted_mean']],orderby=[[m['top10_sort_row'],False]],row_limit=10)
  elif key=='stars':
   p.update(viz_type='echarts_timeseries_bar',x_axis='rating',metrics=[m['rating_count']],groupby=[],orientation='vertical',show_value=True,show_legend=False,x_axis_title='Mức sao',y_axis_title='Số đánh giá',x_axis_sort='rating',x_axis_sort_asc=True,order_desc=False,rich_tooltip=True,y_axis_format=',d',color_scheme='supersetColors',row_limit=5)
   q.update(columns=['rating'],metrics=[m['rating_count']],orderby=[['rating',True]],row_limit=5)
  ctx={'datasource':{'id':ds,'type':'table'},'force':False,'queries':[q],'form_data':p,'result_format':'json','result_type':'full'}
  r=s.request('POST','/api/v1/chart/',{'slice_name':'P1 11A · '+title,'description':'S11A; grain source rating; UTC before aggregation. Fixed catalog excluded from native time filter.' if key=='catalog' else 'S11A; source rating grain, weighted means, no genre duplication. Native UTC time filter before aggregate/top10.','viz_type':p['viz_type'],'datasource_id':ds,'datasource_type':'table','owners':[1],'params':json.dumps(p),'query_context':json.dumps(ctx)})
  ids['charts'][key]=r['id'];configs[key]={'chart_id':r['id'],'form_data':p,'query_context':ctx};(D/'object_ids.json').write_text(json.dumps(ids,indent=2)+'\n',encoding='utf-8')
 pos={'DASHBOARD_VERSION_KEY':'v2','ROOT_ID':{'id':'ROOT_ID','type':'ROOT','children':['GRID_ID']},'GRID_ID':{'id':'GRID_ID','type':'GRID','parents':['ROOT_ID'],'children':['NOTE','ROW1','ROW2','ROW3']},'NOTE':{'id':'NOTE','type':'MARKDOWN','parents':['ROOT_ID','GRID_ID'],'children':[],'meta':{'width':12,'height':20,'code':'### Đánh giá lịch sử · MovieLens 1M\nBộ lọc dùng **thời điểm đánh giá UTC**; từ ngày bắt đầu đến trước ngày kết thúc. **Phim danh mục** cố định 3.883, không chịu bộ lọc.\nTop 10: số đánh giá ↓, điểm trung bình ↓, movie_id ↑. Rating không phải lượt xem; dữ liệu không mô tả nhu cầu hiện tại.','background':'BACKGROUND_TRANSPARENT'}}}
 for row,keys in [('ROW1',['ratings','mean','users']),('ROW2',['movies','catalog','sum']),('ROW3',['top10','stars'])]:
  pos[row]={'id':row,'type':'ROW','parents':['ROOT_ID','GRID_ID'],'children':[],'meta':{'background':'BACKGROUND_TRANSPARENT'}}
  for key in keys:
   node='CHART-'+key;pos[row]['children'].append(node);pos[node]={'id':node,'type':'CHART','parents':['ROOT_ID','GRID_ID',row],'children':[],'meta':{'chartId':ids['charts'][key],'width':(8 if key=='top10' else 4),'height':(60 if row=='ROW3' else 22),'sliceName':key}}
 filt={'id':'NATIVE_FILTER-UTC-RATED','name':'Thời điểm đánh giá (UTC)','filterType':'filter_time','type':'NATIVE_FILTER','targets':[{}],'controlValues':{},'cascadeParentIds':[],'scope':{'rootPath':['ROOT_ID'],'excluded':[ids['charts']['catalog']]},'defaultDataMask':{'extraFormData':{'time_range':'No filter'},'filterState':{'value':'No filter'}}}
 meta={'native_filter_configuration':[filt],'timed_refresh_immune_slices':[],'refresh_frequency':0,'expanded_slices':{},'color_scheme':'supersetColors','chart_configuration':{},'shared_label_colors':{}}
 dash={'dashboard_title':'MovieLens 1M · Tổng quan','slug':'movielens-overview','owners':[1],'published':True,'position_json':json.dumps(pos),'json_metadata':json.dumps(meta)}
 dash['css']=(D/'overview.css').read_text(encoding='utf-8-sig')
 r=s.request('POST','/api/v1/dashboard/',dash);ids['dashboard']=r['id']
 for cid in ids['charts'].values():s.request('PUT','/api/v1/chart/'+str(cid),{'dashboards':[ids['dashboard']]})
 (D/'object_ids.json').write_text(json.dumps(ids,indent=2)+'\n',encoding='utf-8');(D/'chart_definitions.json').write_text(json.dumps(configs,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(D/'dashboard_definition.json').write_text(json.dumps(dash,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'status':'CREATED','object_ids':ids,'dashboard_url':s.base+'/superset/dashboard/'+str(ids['dashboard'])+'/'}))
if __name__=='__main__':main()
