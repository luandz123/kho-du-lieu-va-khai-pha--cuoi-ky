"""Assemble reviewed Markdown chapters; build an editable, field-based DOCX.

Run with the bundled Python runtime. No database or service is accessed.
"""
from pathlib import Path
import re, json, hashlib, subprocess, textwrap
from copy import deepcopy
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'docs/report'
ASSETS = OUT / 'assets'
SOURCES = [ROOT / ('docs/P1/report/chapter_%02d.md' % n if n in (1,3,4)
                   else 'docs/P2/report/chapter_%02d.md' % n) for n in range(1,7)]
REFMAP = {'P2-R01':'R11','P2-R02':'R06','P2-R03':'R12','P2-R04':'R05',
          'P2-R05':'R13','P2-R06':'R03','P2-R07':'R14','P2-R08':'R15'}
EDITS = []

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def replace(s,a,b,reason):
    if a not in s: raise ValueError('Missing editorial anchor: '+a[:70])
    EDITS.append({'before':a,'after':b,'reason':reason})
    return s.replace(a,b)

def clean(s, path):
    # Mapping before any overlapping Rnn references.
    for a,b in REFMAP.items(): s=s.replace(a,b)
    s=s.replace('P2-R03–R05','R12, R05, R13')
    s=s.replace('R12–R05','R12, R05, R13')
    s=s.replace('R14–R08','R14–R15')
    # Preserve working relative links in the combined source Markdown.
    def link(m):
        label,target=m.group(1),m.group(2)
        if '://' not in target and not target.startswith('#'):
            target=Path(__import__('os').path.relpath((path.parent/target).resolve(), OUT)).as_posix()
        return '['+label+']('+target+')'
    s=re.sub(r'(?<!!)\[([^\]]+)\]\(([^)]+)\)',link,s)
    s=re.sub(r'!\[([^\]]*)\]\(([^)]+)\)',lambda m:'!['+m[1]+']('+Path(__import__('os').path.relpath((path.parent/m[2]).resolve(),OUT)).as_posix()+')',s)
    return s

def chapter(n):
    p=SOURCES[n-1]; s=p.read_text(encoding='utf-8')
    if n==1:
        a='Đối với báo cáo, P1 viết chương 1, 3, 4; P2 viết chương 2, 5, 6. P1 chỉ ghép bản tổng sau khi hai phần được duyệt. Nội dung thuật toán và phân tích thực nghiệm Q1/Q2 được trình bày tập trung ở chương 5; chương 4 chỉ mô tả giao diện và cách sử dụng kết quả cụm trong BI để tránh lặp phần khai phá.'
        s=replace(s,a,'P1 phụ trách DW, ETL, OLAP và BI; P2 phụ trách dữ liệu và các mô hình khai phá. Nội dung thuật toán và thực nghiệm Q1/Q2 được trình bày tập trung ở chương 2 và chương 5; chương 4 mô tả giao diện và cách sử dụng kết quả cụm trong BI.','Bỏ nhật ký phân công viết và duyệt khỏi thân báo cáo; giữ phân công kỹ thuật.')
        s=replace(s,'Candidate thực chạy là `4546d5bbd8f9130a420518b77dc3ad894bc7f42b` (merge PR25), khác commit công bố hồ sơ nghiệm thu PR30.','Candidate thực chạy giữ nguyên như phụ lục A; commit tài liệu không đại diện một lần thực nghiệm mới.','Đưa SHA/PR về phụ lục.')
        s=replace(s,'bản tổng chỉ được ghép sau khi nhận đủ phần P2 được duyệt.','báo cáo tổng hiện chờ review và G5 chưa hoàn thành.','Cập nhật trạng thái đã được giao ghép, không tuyên bố G5 đạt.')
    if n==2:
        s=replace(s,'Mã tài liệu P2-R được giải thích trong [danh mục tham khảo](references.md).','Mã tài liệu R và bằng chứng E được giải thích trong tài liệu tham khảo và phụ lục.','Thống nhất hệ mã nguồn.')
        s=replace(s,' PCA hai chiều chỉ minh họa phép chiếu, không là không gian fit và không chứng minh các cụm tách biệt hoàn toàn.','','Loại PCA khỏi bản chính theo yêu cầu, không sử dụng kết quả PCA đang mâu thuẫn.')
    if n==3:
        s=replace(s,'sau PR28/PR29; G4 đạt','theo hồ sơ nghiệm thu tích hợp; G4 đạt','Bỏ nhật ký PR khỏi thân báo cáo.')
        s=replace(s,'Candidate thực chạy vẫn là merge PR25, không thay bằng commit hồ sơ.','Candidate thực chạy được giữ riêng trong phụ lục A, không thay bằng commit hồ sơ.','Chuyển mốc Git về phụ lục.')
        old=next(x for x in s.splitlines() if x.startswith('Các dimension không chứa'))
        s=replace(s,old,'Thiết kế chỉ dùng thuộc tính có trong nguồn, không thêm đạo diễn, diễn viên, phiên xem hoặc doanh thu và không theo dõi lịch sử thay đổi nhân khẩu học. Full refresh phục vụ snapshot dự án; chưa triển khai SCD/incremental đầy đủ. Kết quả tái lập Windows độc lập của P2 đã được nghiệm thu trong G4 (I01–I15); không suy rộng sang Linux hoặc phục hồi toàn stack trên máy mới. Mốc thực chạy giữ tại phụ lục A; thực thi và OLAP ở chương 4. [Nguồn: [ma trận nghiệm thu](../integration_acceptance.md), [ghi nhận G4](../g4_acceptance_20261024.json).]','Rút gọn kết đoạn chương 3, giữ giới hạn kỹ thuật và nghiệm thu; tránh lặp trạng thái G4 và đoạn lẻ trên trang gần trống.')
    if n==4:
        s=replace(s,'[g 3_transaction.py]','[g3_transaction.py]','Sửa lỗi khoảng trắng tên nguồn.')
        s=replace(s,'Candidate thực chạy giữ nguyên `4546d5bbd8f9130a420518b77dc3ad894bc7f42b`; commit merge hồ sơ PR30 không phải một lượt chạy mới.','Candidate thực chạy giữ nguyên như phụ lục A; cập nhật hồ sơ không phải một lượt chạy mới.','Chuyển SHA/PR khỏi thân báo cáo.')
    if n==5:
        first=s.split('\n')[2]
        s=replace(s,first,'Chương này trình bày thực nghiệm đã công bố cho Q1 và Q2. Công thức và ví dụ minh họa nằm ở chương 2; mã E12–E16 liên kết với danh mục bằng chứng trong phụ lục. Candidate thực kiểm được giữ riêng như phụ lục A.','Bỏ nhật ký viết báo cáo khỏi mở đầu; giữ nguồn kết quả và candidate.')
        s=replace(s,'Receipt duy nhất dùng cho bảng sau là run `test_run_s10b_official_20261022_034458`, status OFFICIAL_COMPLETED.','Bảng sau tham chiếu receipt Test chính thức OFFICIAL_COMPLETED; run và hash truy vết được ghi ở phụ lục.','Đưa run dài về phụ lục, không thay metric.')
        s=replace(s,'Log 31 unit test là bằng chứng lịch sử, không phải test mới chạy khi viết báo cáo.','Hồ sơ tái lập độc lập ghi nhận 31 unit test; đó là bằng chứng của lượt kiểm trên P2.','Diễn đạt kết quả, bỏ nhật ký biên tập.')
        s=replace(s,'sample hash `afc27da1977cf28e45417b7eaf9ff27faa6028dc4e670367a223c758078db485`','fingerprint mẫu được ghi tại phụ lục B','Đưa hash dài về phụ lục, giữ mẫu cố định và seed.')
        # Approved presentation-only corrections; the reviewed P2 chapter is untouched.
        for old,new in [('t≤974862386','t ≤ t₁'),('974862386<t≤976422051','t₁ < t ≤ t₂'),('t>976422051','t > t₂')]:
            s=replace(s,old,new,'Bảng 5.5 dùng ký hiệu ngưỡng thay số dài; giữ nguyên giá trị trong giải thích dưới bảng.')
        s=replace(s,'t₁=`2000-11-22T03:06:26Z`, t₂=`2000-12-10T04:20:51Z`','t là timestamp giây Unix; t₁=`974862386` (`2000-11-22T03:06:26Z`), t₂=`976422051` (`2000-12-10T04:20:51Z`)','Giữ đủ giây Unix và UTC của hai ngưỡng đóng băng ngoài ô điều kiện.')
        table_start=s.index('| Mô hình | neighbor_k | Precision@5 | Recall@5 (công bố) |')
        table_end=s.index('\n\n',table_start)
        old=s[table_start:table_end]
        rows=[parse_row(line) for line in old.splitlines()]
        # Keep unrounded values verbatim in one unbroken code run each.
        long_values=[(r[1],r[4]) for r in rows[2:] if r[0]=='CF']
        compact='\n'.join('| '+' | '.join(r[:4]+r[5:])+' |' for r in rows)
        note='\n\nRecall@5 chưa làm tròn của từng cấu hình được giữ nguyên tại phụ lục G để đọc trọn số; bảng này dùng giá trị công bố. Tiêu chí chọn k vẫn dựa trên Recall validation chưa làm tròn, không đổi theo cách trình bày.'
        s=replace(s,old,compact+note,'Bảng 5.7 chuyển ba số Recall chưa làm tròn nguyên giá trị sang phụ lục G; không đổi tiêu chí chọn k.')
    if n==6:
        s=replace(s,'[S13](../../agent/steps/P2/S13.md), [REVIEWS_P2](../../agent/REVIEWS_P2.md)','[ghi nhận G4](../../P1/g4_acceptance_20261024.json)','Dẫn ghi nhận nghiệm thu thay nhật ký review trong thân báo cáo.')
        s=replace(s,'Ổn định seed trên snapshot chưa chứng minh ổn định khi dữ liệu thay đổi; PCA không thay thế chỉ số toàn không gian.','Ổn định seed trên snapshot chưa chứng minh ổn định khi dữ liệu thay đổi.','Loại PCA khỏi bản chính, giữ giới hạn của bằng chứng seed.')
        s=replace(s,'Candidate thực kiểm giữ nguyên `4546d5bbd8f9130a420518b77dc3ad894bc7f42b`. Commit merge hồ sơ và HEAD viết báo cáo không thay thế candidate hoặc các code hash của run lịch sử.','Candidate thực kiểm và code hash của run lịch sử được giữ nguyên trong phụ lục A, tách biệt với phiên bản tài liệu.','Chuyển Git dài khỏi thân báo cáo.')
    return clean(s,p)

def references():
    s=(ROOT/'docs/P1/report/references.md').read_text(encoding='utf-8')
    # Keep actual reference records only, not editorial instructions or review logs.
    ext=[]; internal=[]
    for para in re.split(r'\n\s*\n',s):
        if re.match(r'\*\*R\d\d\.',para):
            para=re.sub(r' README được truy cập; trang giới thiệu được tìm thấy nhưng lần mở trực tiếp bị timeout\.','',para)
            ext.append(clean(para,ROOT/'docs/P1/report/references.md'))
        if re.match(r'\*\*I\d\d\.',para): internal.append(clean(para,ROOT/'docs/P1/report/references.md'))
    p2=(ROOT/'docs/P2/report/references.md').read_text(encoding='utf-8')
    for old in ['P2-R01','P2-R03','P2-R05','P2-R07','P2-R08']:
        para=next(p for p in p2.splitlines() if p.startswith('- **'+old+'.'))
        para=para.removeprefix('- ')
        para=re.sub(r' Đã đọc.*?(?= Dự án| ARI dự án| Không gọi|$)','',para)
        ext.append(clean(para,ROOT/'docs/P2/report/references.md'))
    internal.append('**I06.** P2. Dữ liệu chia thời gian, validation, đánh giá chính thức và tái lập độc lập. `results/mining/split_manifest.json`; `cf_validation_experiments.json`; `baseline_popularity_validation.json`; `cf_test_evaluation_receipt.json`; `results/mining/integration_p2/manifest.json`; `docs/P2/integration_report.md`. Tương ứng E14–E16/E20; metrics Test là kết quả tham chiếu, không đánh giá lại.')
    return '# Tài liệu tham khảo\n\n## Nguồn dữ liệu nghiên cứu và tài liệu chính thức\n\n'+'\n\n'.join(ext)+'\n\n## Tài liệu và bằng chứng nội bộ\n\nMã I chỉ nguồn nội bộ của nhóm; mã E ánh xạ phép kiểm và artifact trong phụ lục. Các tài liệu này không thay rubric chính thức của giảng viên. Ngày tra cứu nguồn web của hai phần: 24/10/2026.\n\n'+'\n\n'.join(internal)

def appendix():
    p=ROOT/'docs/P1/report/appendix_sources.md'; s=p.read_text(encoding='utf-8')
    s=s.replace('# Phụ lục truy vết cho phần báo cáo P1','# Phụ lục truy vết dữ liệu và thực nghiệm')
    s=s.replace('Phụ lục tập hợp identity, hash, nguồn kiểm chứng và lệnh dài của chương 1, 3, 4. Lệnh được trích để tái lập khi có cấu hình và phạm vi thực thi hợp lệ, không là bằng chứng đã chạy trong lượt biên tập. Hồ sơ review và trạng thái công bố tách tại [editorial_notes.md](editorial_notes.md).','Phụ lục tập hợp identity, hash, nguồn kiểm chứng và lệnh tái lập của báo cáo. Lệnh chỉ dùng khi có cấu hình cục bộ và phạm vi thực thi hợp lệ; việc liệt kê lệnh không là bằng chứng đã chạy lại.')
    s='\n'.join(x for x in s.splitlines() if '| Dàn ý13A |' not in x)
    s=clean(s,p)
    s=s.replace('## C. Lệnh và khả năng tái lập','Fingerprint mẫu Silhouette 2.000 người, seed42: `afc27da1977cf28e45417b7eaf9ff27faa6028dc4e670367a223c758078db485`. Nguồn: experiments_summary trong results/mining/clustering_summary.json.\n\n## C. Lệnh và khả năng tái lập')
    s+='\n\n## E. Đối chiếu bằng chứng cho sáu chương\n\n| Mã | Nội dung | Nguồn trong repository |\n|---|---|---|\n'
    rows=[('E01','Phạm vi và tiêu chí nội bộ','docs/project_spec.md; docs/acceptance.md'),('E02','Nguồn và hash gốc','data/source_manifest.json'),('E03','EDA và canonical','results/eda/data_profile.csv; eda_metrics.json; canonical_manifest.json'),('E04','Giao diện và serializer','docs/shared/data_contract.md; mining/data_io.py'),('E05','Thiết kế DW','database/schema.sql; erd.md; data_dictionary.md; source_to_target.md'),('E06','Staging và rollback','results/warehouse/s05_summary.json'),('E07','Full refresh và rollback toàn pipeline','results/warehouse/s06d_summary.json; s06d_rollback_5c9c553454e54e81953fded2d524877c.json'),('E08','Gói DW','results/warehouse/dw_manifest.json; docs/P1/dw_handoff.md'),('E09','SQL và fixture OLAP','olap/queries.sql; database/views.sql; tests/warehouse/'),('E10','O1–O4/O6','results/olap/s07_af6dbc20b40d4a47aa3ea71bde6fd107/report.json'),('E11','Q3 theo quý','docs/P1/olap_findings.md; dashboard/trends/evidence/reconciliation.json'),('E12','Đặc trưng và K-Means','mining/features.py; results/mining/clustering_summary.json; docs/P2/clustering_interpretation.md'),('E13','G3 và model active','results/warehouse/s11b2/handoff_summary.json; etl/g3_transaction.py'),('E14','Split và validation','results/mining/split_manifest.json; cf_validation_experiments.json; baseline_popularity_validation.json'),('E15','Test chính thức','results/mining/cf_test_evaluation_receipt.json; cf_test_evaluation.json; evaluator_provenance_trace.json'),('E16','CLI qua DW','results/mining/integration_p2/cli_verification_summary.json; docs/P2/integration_report.md'),('E17','Ba dashboard và filter','dashboard/overview/README.md; dashboard/trends/README.md; dashboard/preferences/README.md; evidence/reconciliation.json trong từng thư mục'),('E18','Hai chu trình P1','results/warehouse/s12a/57c1e8e3d3f445c4b3eeddbfc3364709/summary.json; environment.json; postflight.json'),('E19','Ba cơ chế phục hồi','docs/P1/integration_prep/README.md; dashboard/metadata_restore/README.md; dashboard/restore/README.md'),('E20','Tái lập P2 và nghiệm thu G4','results/mining/integration_p2/manifest.json; docs/P2/integration_report.md; docs/P1/integration_acceptance.md; g4_acceptance_20261024.json')]
    for a,b,c in rows:s+='| '+a+' | '+b+' | '+c+' |\n'
    s+='\n## F. Nguồn chương và phiên bản tài liệu\n\nPhần P1 kế thừa chương 1/3/4 và phụ lục đã duyệt tại HEAD `d018921be66b12dc275933e1de9c2e755b74241a`, bổ sung hình/checklist đã merge cùng PR27 tại `03d9bc9932f7919c5eb5d04075f0235a1e0448fc` và cập nhật G4 cục bộ theo nghiệm thu ngày 24/10/2026. Phần P2 chương 2/5/6 lấy từ HEAD được duyệt `f090eff8b5a58242f8391469772cb3bd329f43f4`, PR31 merge `a2021a9f591c56222f5ae16e169f278bf3cec5a7`. Đây là nguồn biên tập, không thay candidate thực chạy.\n\nBản tổng WAITING_REVIEW; G4 ĐẠT trong phạm vi I01–I15, G5 chưa hoàn thành. Nguồn chương riêng được bảo toàn; mọi thay đổi biên tập bản tổng nằm trong editorial_manifest.json.\n'
    s+='\n## G. Recall validation chưa làm tròn\n\nCác số dưới đây chép nguyên giá trị từ bảng 5.7 của chương P2 được duyệt và cf_validation_experiments.json; không phải kết quả chạy lại. Mẫu số/cohort giữ theo chương 2 và mục 5.5, 471 người đủ điều kiện.\n\n'
    original=SOURCES[4].read_text(encoding='utf-8');start=original.index('| Mô hình | neighbor_k | Precision@5 | Recall@5 (công bố) |');end=original.index('\n\n',start)
    for row in [parse_row(line) for line in original[start:end].splitlines()]:
        if row[0]=='CF':s+='- neighbor_k='+row[1]+': `'+row[4]+'`.\n'
    s+='\nBaseline: Không có trường này trong artifact baseline; không suy số chưa làm tròn từ giá trị công bố. Trong lưới CF, neighbor_k=40 có Recall validation chưa làm tròn cao nhất; hòa thì chọn k nhỏ hơn. Top-N=5 và các metric Test không thay đổi.\n'
    return s

def font(size,bold=False): return ImageFont.truetype('C:/Windows/Fonts/'+('arialbd.ttf' if bold else 'arial.ttf'),size)
def diagram(name,nodes,edges,size):
    im=Image.new('RGB',size,'white'); d=ImageDraw.Draw(im)
    for a,b,label in edges:
        x,y,w,h,_=nodes[a]; X,Y,W,H,_=nodes[b]
        # Orthogonal routing, explicit FK cardinalities in labels.
        start=(x+w//2,y+h); end=(X+W//2,Y)
        if Y<y+h: start=(x+w,y+h//2); end=(X,Y+H//2)
        mid=((start[0]+end[0])//2,(start[1]+end[1])//2)
        d.line([start,(start[0],mid[1]),(end[0],mid[1]),end],fill='#67798a',width=4)
        d.polygon([(end[0],end[1]),(end[0]-7,end[1]-12),(end[0]+7,end[1]-12)],fill='#67798a')
        if label: d.text((mid[0]+8,mid[1]+4),label,font=font(23),fill='#334455')
    for x,y,w,h,text in nodes.values():
        d.rounded_rectangle((x,y,x+w,y+h),12,fill='#f3f5f7',outline='#52697e',width=3)
        lines=text.split('\n'); yy=y+16
        for j,line in enumerate(lines):
            d.text((x+18,yy),line,font=font(27 if j==0 else 24,j==0),fill='black'); yy+=38
    im.save(ASSETS/name)

def diagrams():
    diagram('architecture.png',{
      'raw':(350,20,700,90,'MovieLens 1M và manifest'),
      'st':(350,160,700,95,'Staging → DW → 4 view contract v2'),
      'o':(30,330,390,130,'OLAP O1–O6\nCount · mean · QoQ'),
      'q1':(500,330,400,130,'Q1 — K-Means\nVector tỷ lệ genre'),
      'q2':(980,330,400,130,'Q2 — CF + baseline\nTemporal split'),
      'b':(30,550,390,130,'Superset\nTổng quan · Xu hướng'),
      'g':(500,550,400,130,'G3 → analytics\nRegistry · active views'),
      'c':(980,550,400,130,'CLI Top 5\nEvaluation ≠ demo'),
      'p':(500,770,400,100,'Superset Sở thích')},
      [('raw','st',''),('st','o',''),('st','q1',''),('st','q2',''),('o','b',''),('q1','g',''),('g','p',''),('q2','c','')],(1420,900))
    nodes={
      'u':(20,20,410,170,'DIM_USER\nPK user_key · UQ user_id\nF/M · tuổi · occupation'),
      'm':(500,20,410,170,'DIM_MOVIE\nPK movie_key · UQ movie_id\nTitle · release_year NULL'),
      'd':(980,20,410,170,'DIM_DATE\nPK date_key · UQ full_date\nNăm · quý · tháng · ngày'),
      'f':(500,300,410,200,'FACT_RATING\nPK rating_key\nFK user/movie/date + UTC\nUQ user_key, movie_key'),
      'b':(500,590,410,170,'BRIDGE_MOVIE_GENRE\nPK/FK movie_key,genre_key\nMỗi cặp đúng một lần'),
      'g':(20,590,410,170,'DIM_GENRE\nPK genre_key · UQ tên'),
      'r':(500,850,410,170,'MODEL_REGISTRY\nPK model_version\nIdentity · active · valid'),
      'uc':(20,1100,410,170,'USER_CLUSTER\nPK version,user_id\nFK registry + dim_user'),
      'cp':(980,1100,410,170,'CLUSTER_GENRE_PROFILE\nPK version,cluster,genre\nFK registry + dim_genre')}
    diagram('erd.png',nodes,[],(1420,1300))
    im=Image.open(ASSETS/'erd.png');d=ImageDraw.Draw(im)
    routes=[([(225,190),(225,245),(650,245),(650,300)],(300,213)),
            ([(705,190),(705,300)],(715,225)),
            ([(1185,190),(1185,265),(780,265),(780,300)],(1000,232)),
            ([(910,105),(945,105),(945,675),(910,675)],(950,400)),
            ([(430,675),(500,675)],(434,637)),
            ([(20,105),(5,105),(5,1185),(20,1185)],(22,1045)),
            ([(225,760),(225,805),(1410,805),(1410,1185),(1390,1185)],(1200,770)),
            ([(650,1020),(650,1060),(225,1060),(225,1100)],(450,1026)),
            ([(780,1020),(780,1060),(1185,1060),(1185,1100)],(950,1026))]
    for points,label in routes:
        d.line(points,fill='#67798a',width=3)
        x,y=points[-1];px,py=points[-2]
        if x==px: triangle=[(x,y),(x-6,y-10),(x+6,y-10)]
        elif x>px: triangle=[(x,y),(x-10,y-6),(x-10,y+6)]
        else: triangle=[(x,y),(x+10,y-6),(x+10,y+6)]
        d.polygon(triangle,fill='#67798a');d.text(label,'1 : N',font=font(22),fill='#334455')
    im.save(ASSETS/'erd.png')

def add_field(p,instruction):
    run=OxmlElement('w:r'); fld=OxmlElement('w:fldChar');fld.set(qn('w:fldCharType'),'begin');run.append(fld);p._p.append(run)
    run=OxmlElement('w:r'); t=OxmlElement('w:instrText');t.set(qn('xml:space'),'preserve');t.text=' '+instruction+' ';run.append(t);p._p.append(run)
    for typ in ['separate','end']:
        run=OxmlElement('w:r');fld=OxmlElement('w:fldChar');fld.set(qn('w:fldCharType'),typ);run.append(fld);p._p.append(run)

def inline(p,text):
    # URLs are retained as links in source Markdown and references; visible body uses labels.
    text=re.sub(r'\[([^\[\]]+)\]\(([^)]+)\)',r'\1',text)
    for part in re.split(r'(\*\*.*?\*\*|`[^`]+`|\*[^*]+\*)',text):
        if not part: continue
        r=p.add_run(part.strip('*') if part.startswith('*') else part.strip('`') if part.startswith('`') else part)
        if part.startswith('**'):r.bold=True
        elif part.startswith('*'):r.italic=True
        if part.startswith('`'):r.font.name='Consolas';r.font.size=Pt(9)
    return p

def caption(doc,text,kind):
    text=text.strip('* ')
    text=re.sub(r'\[([^\[\]]+)\]\(([^)]+)\)',r'\1',text)
    text=text.replace('`','').replace('**','')
    # Keep titles compact in automatically populated figure/table lists.
    m=re.match(r'((?:Hình|Bảng) \d+\.\d+\.\s*[^.]+\.)(.*)',text)
    title=m[1] if m else text
    extra=m[2].strip() if m else ''
    if kind=='figure':
        label=re.match(r'Hình (\d+\.\d+)\.',text)[1]
        titles={'1.1':'Kiến trúc dữ liệu và hai nhánh khai phá',
                '3.1':'Phân bố số đánh giá theo mức sao','3.2':'Hoạt động đánh giá theo quý UTC',
                '3.3':'ERD kho dữ liệu và kết quả cụm','4.1':'Dashboard Tổng quan toàn lịch sử',
                '4.2':'Dashboard Xu hướng với bộ lọc quý và thể loại',
                '4.3':'Dashboard Sở thích toàn bộ cohort',
                '4.4':'Dashboard Sở thích lọc cụm 1 giới F tuổi 25–34',
                '5.1':'SSE và Silhouette của 14 cấu hình K-Means'}
        title='Hình '+label+'. '+titles[label]+'.'
        extra=re.sub(r'^Hình \d+\.\d+\.\s*','',text)
    p=doc.add_paragraph(style='Figure Caption' if kind=='figure' else 'Table Caption'); inline(p,title)
    p.paragraph_format.keep_with_next=True
    if extra:
        p=doc.add_paragraph(style='Source Note');inline(p,extra)
        p.paragraph_format.keep_with_next=kind=='table'

def atom(s):
    r=OxmlElement('m:r');t=OxmlElement('m:t');t.set(qn('xml:space'),'preserve');t.text=s;r.append(t);return r
def container(tag,items):
    e=OxmlElement('m:'+tag)
    for item in items:e.append(atom(item) if isinstance(item,str) else item)
    return e
def sub(base,idx):return container('sSub',[container('e',[base]),container('sub',[idx])])
def sup(base,idx):return container('sSup',[container('e',[base]),container('sup',[idx])])
def fraction(num,den):return container('f',[container('num',num),container('den',den)])
def summation(low,high,body):
    n=OxmlElement('m:nary');pr=OxmlElement('m:naryPr')
    for tag,val in [('chr','∑'),('limLoc','subSup'),('supHide','0' if high else '1')]:
        e=OxmlElement('m:'+tag);e.set(qn('m:val'),val);pr.append(e)
    n.append(pr);n.append(container('sub',low));n.append(container('sup',high));n.append(container('e',body));return n
def formulas():
    normx=container('box',[container('e',['‖',sub('x','u'),' − ',sub('μ','c'),'‖₂'])])
    return [
      [[sub('C','u,g'),' = ',summation(['i ∈ P(u)'],[],['1[g ∈ G(i)]']),' ;   ',sub('S','u'),' = ',summation(['g = 1'],['18'],[sub('C','u,g')])],
       [sub('p','u,g'),' = ',fraction([sub('C','u,g')],[sub('S','u')]),'   (',sub('S','u'),' > 0)']],
      [['J = ',summation(['c = 1'],['K'],[summation(['u ∈ ',sub('C','c')],[],[sup(normx,'2')])])],
       [sub('μ','c'),' = ',fraction(['1'],['|',sub('C','c'),'|']),summation(['u ∈ ',sub('C','c')],[],[sub('x','u')])]],
      [['sim(i,j) = ',fraction([sub('R','i'),' · ',sub('R','j')],['‖',sub('R','i'),'‖₂ ‖',sub('R','j'),'‖₂'])]],
      [['score(u,i) = ',summation(['j ∈ S(u)'],[],['1[i ∈ ',sub('N','k'),'(j)] sim(i,j)'])]],
      [['P@5(u) = ',fraction(['h(u)'],['5']),' ;   R@5(u) = ',fraction(['h(u)'],['|T(u)|'])]],
      [['macro P@5 = ',fraction(['1'],['|U|']),summation(['u ∈ U'],[],['P@5(u)'])],
       ['macro R@5 = ',fraction(['1'],['|U|']),summation(['u ∈ U'],[],['R@5(u)'])]]]

def parse_row(row):
    cells=[];buf='';code=False
    for char in row.strip().strip('|'):
        if char=='`':code=not code
        if char=='|' and not code:cells.append(buf.strip());buf=''
        else:buf+=char
    cells.append(buf.strip());return cells

def table(doc,rows):
    rows=[parse_row(r) for r in rows]
    rows=[r for r in rows if not all(re.fullmatch(r':?-+:?',c.replace(' ','')) for c in r)]
    cols=len(rows[0]); t=doc.add_table(rows=0,cols=cols);t.autofit=False
    # Weight by typical text length; keep numeric columns compact.
    weights=[]
    for j in range(cols):
        lengths=[len(r[j]) for r in rows if j<len(r)]
        numeric=sum(bool(re.fullmatch(r'[\d.,%+−–— /≈:]+',r[j])) for r in rows[1:] if j<len(r))
        weights.append(0.7 if numeric>len(rows[1:])*0.65 else min(3.5,max(1.1,sum(lengths)/len(lengths)/25)))
    total=sum(weights); widths=[16.0*w/total for w in weights]
    for j,w in enumerate(widths): t.columns[j].width=Cm(w)
    for i,row in enumerate(rows):
        cells=t.add_row().cells
        for j,cell in enumerate(cells):
            cell.width=Cm(widths[j]); tcPr=cell._tc.get_or_add_tcPr()
            borders=OxmlElement('w:tcBorders')
            for side in ('top','left','bottom','right'):
                el=OxmlElement('w:'+side);el.set(qn('w:val'),'single');el.set(qn('w:sz'),'4');el.set(qn('w:color'),'D9D9D9');borders.append(el)
            tcPr.append(borders)
            margins=OxmlElement('w:tcMar')
            for side in ['top','left','bottom','right']:
                el=OxmlElement('w:'+side);el.set(qn('w:w'),'75');el.set(qn('w:type'),'dxa');margins.append(el)
            tcPr.append(margins)
            shade=OxmlElement('w:shd');shade.set(qn('w:fill'),'E8EDF2' if i==0 else 'F7F8FA' if i%2==0 else 'FFFFFF');tcPr.append(shade)
            p=cell.paragraphs[0];p.style='Table Text';inline(p,row[j] if j<len(row) else '')
            if i==0:p.paragraph_format.keep_with_next=True
            for r in p.runs:
                r.font.size=Pt(10 if cols<7 else 9)
                if i==0:r.bold=True
            if i and re.fullmatch(r'[\d.,%+−–— /≈:]+',row[j] if j<len(row) else ''):p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        if i==0:
            el=OxmlElement('w:tblHeader');t.rows[i]._tr.get_or_add_trPr().append(el)
        else:
            el=OxmlElement('w:cantSplit');t.rows[i]._tr.get_or_add_trPr().append(el)
    doc.add_paragraph().paragraph_format.space_after=Pt(2)

def build_doc(md):
    doc=Document();sec=doc.sections[0]
    sec.page_width=Cm(21);sec.page_height=Cm(29.7)
    sec.top_margin=Cm(2.2);sec.bottom_margin=Cm(2);sec.left_margin=Cm(2.6);sec.right_margin=Cm(2.4)
    normal=doc.styles['Normal'];normal.font.name='Times New Roman';normal.font.size=Pt(12)
    normal.paragraph_format.line_spacing=1.15;normal.paragraph_format.space_after=Pt(6)
    for name,size in [('Title',23),('Subtitle',14),('Heading 1',16),('Heading 2',14),('Heading 3',12.5)]:
        st=doc.styles[name];st.font.name='Times New Roman';st.font.size=Pt(size);st.font.color.rgb=RGBColor(0,0,0)
        st.paragraph_format.keep_with_next=True
    for st in doc.styles:
        if st.type==WD_STYLE_TYPE.PARAGRAPH:
            fonts=st.element.get_or_add_rPr().find(qn('w:rFonts'))
            if fonts is None: fonts=OxmlElement('w:rFonts');st.element.get_or_add_rPr().append(fonts)
            for key in list(fonts.attrib):
                if 'theme' in key.lower():del fonts.attrib[key]
            for key in ['ascii','hAnsi','eastAsia','cs']:fonts.set(qn('w:'+key),'Times New Roman')
            for border in st.element.findall('.//'+qn('w:pBdr')):border.getparent().remove(border)
    for name,size in [('Figure Caption',11),('Table Caption',11),('Source Note',10),('Table Text',10),('Code Block',9)]:
        st=doc.styles.add_style(name,WD_STYLE_TYPE.PARAGRAPH);st.base_style=normal;st.font.size=Pt(size)
        st.paragraph_format.line_spacing=1.05;st.paragraph_format.space_after=Pt(4)
        if name.endswith('Caption'):st.font.bold=True
    doc.styles['Code Block'].font.name='Consolas'
    sec.different_first_page_header_footer=True
    p=sec.footer.paragraphs[0];p.alignment=WD_ALIGN_PARAGRAPH.CENTER;add_field(p,'PAGE')
    for line in ['Trường: ........................................................', 'Khoa / Bộ môn: .............................................']:
        p=doc.add_paragraph(line);p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph('\n')
    p=doc.add_paragraph('BÁO CÁO BÀI TẬP LỚN',style='Subtitle');p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    p=doc.add_paragraph('KHO DỮ LIỆU VÀ KHAI PHÁ DỮ LIỆU',style='Title');p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    p=doc.add_paragraph('Phân tích đánh giá và gợi ý phim trên MovieLens 1M',style='Subtitle');p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph('\n')
    for s in ['Giảng viên hướng dẫn: ........................................................',
              'Sinh viên 1 — Họ tên và MSSV: .............................................',
              'Sinh viên 2 — Họ tên và MSSV: .............................................',
              'Lớp / nhóm: ............................................................................',
              'Ngày bảo vệ: 27/10/2026']:
        doc.add_paragraph(s)
    doc.add_paragraph('Tháng 10 năm 2026').alignment=WD_ALIGN_PARAGRAPH.CENTER
    doc.add_page_break()
    doc.add_heading('Tóm tắt',level=1)
    doc.add_paragraph('Đồ án xây dựng luồng phân tích MovieLens 1M gồm 1.000.209 đánh giá, 6.040 người dùng và 3.883 phim. PostgreSQL lưu staging và kho dữ liệu; Python thực hiện ETL, đối soát, K-Means và gợi ý item-based Collaborative Filtering; Superset cung cấp ba dashboard. Grain của fact là một đánh giá nguồn, còn quan hệ phim nhiều thể loại được tách qua bridge để giữ đúng phép đếm.')
    doc.add_paragraph('Kết quả Q1 mô tả bốn nhóm sở thích trên 6.038 người đủ bằng chứng. Q2 so sánh CF k40 với Popularity Baseline trên cùng giao thức chia thời gian và cohort; metrics Test được tham chiếu từ receipt chính thức. Q3 phân tích số đánh giá theo quý bằng count, tỷ trọng và QoQ có xử lý quý biên. Tích hợp G4 đã được nghiệm thu ngày 24/10/2026 trong phạm vi I01–I15; báo cáo tổng đang chờ review, G5 chưa hoàn thành.')
    doc.add_paragraph('Từ khóa: MovieLens 1M; kho dữ liệu; ETL; OLAP; K-Means; item-based CF; Apache Superset.')
    for title,instr in [('Mục lục','TOC \\o "1-3" \\h \\z \\u'),('Danh mục hình','TOC \\t "Figure Caption,1" \\h \\z'),('Danh mục bảng','TOC \\t "Table Caption,1" \\h \\z')]:
        doc.add_page_break();doc.add_paragraph(title,style='Title');add_field(doc.add_paragraph(),instr)
    doc.add_page_break()
    lines=md.splitlines();i=0;eq=0;mermaid=0
    while i<len(lines):
        line=lines[i].strip()
        if not line:i+=1;continue
        if line.startswith('```'):
            typ=line[3:];block=[];i+=1
            while i<len(lines) and not lines[i].startswith('```'):block.append(lines[i]);i+=1
            if typ=='mermaid':
                name=['architecture.png','erd.png'][mermaid];mermaid+=1
                p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER
                p.add_run().add_picture(str(ASSETS/name),width=Cm(16));p.paragraph_format.keep_with_next=True
            else:
                for b in block:doc.add_paragraph(b,style='Code Block')
            i+=1;continue
        if line.startswith('$$'):
            for elements in formulas()[eq]:
                p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER
                math=OxmlElement('m:oMathPara');math.append(container('oMath',elements));p._p.append(math)
            eq+=1;i+=1;continue
        if line.startswith('|'):
            rows=[]
            while i<len(lines) and lines[i].strip().startswith('|'):rows.append(lines[i]);i+=1
            table(doc,rows);continue
        m=re.match(r'^(#{1,3})\s+(.+)',line)
        if m:
            level=len(m[1]);heading=m[2]
            if level==1 and len(doc.paragraphs)>20:
                # Chapter starts on a fresh page; no forced blank odd pages.
                if not heading.startswith('Chương 1'):doc.add_page_break()
            p=doc.add_heading(heading,level=level);i+=1;continue
        m=re.match(r'!\[([^\]]*)\]\(([^)]+)\)',line)
        if m:
            img=(OUT/m[2]).resolve();im=Image.open(img);w,h=im.size
            width=min(16,13.7*w/h)
            p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.add_run().add_picture(str(img),width=Cm(width));p.paragraph_format.keep_with_next=True
            i+=1;continue
        if re.match(r'^\*?\*?(Hình|Bảng) \d+\.\d+\.',line):
            caption(doc,line,'figure' if 'Hình' in line[:8] else 'table');i+=1;continue
        if line.startswith('- '):inline(doc.add_paragraph(style='List Bullet'),line[2:]);i+=1;continue
        p=doc.add_paragraph();inline(p,line)
        if re.match(r'^\[?Nguồn(?: bảng)?\s*:',line):p.style='Source Note'
        # URLs are displayed only in the bibliography, never in a long table cell.
        if line.startswith('**R'):
            urls=re.findall(r'\]\((https?://[^)]+)\)',line)
            if urls:
                q=doc.add_paragraph(style='Source Note')
                for u in urls:q.add_run(u+'\n')
        i+=1
    settings=doc.settings.element;upd=OxmlElement('w:updateFields');upd.set(qn('w:val'),'true');settings.append(upd)
    doc.core_properties.title='Phân tích đánh giá và gợi ý phim trên MovieLens 1M'
    doc.core_properties.author='Nhóm đồ án';doc.core_properties.last_modified_by='Nhóm đồ án'
    doc.save(OUT/'bao_cao_tong_hop.docx')
    return eq

def main():
    OUT.mkdir(exist_ok=True);ASSETS.mkdir(exist_ok=True)
    diagrams()
    body='\n\n'.join(chapter(n) for n in range(1,7))
    if 'PCA' in body: raise ValueError('PCA must be excluded from the main report')
    md=body+'\n\n'+appendix()+'\n\n'+references()+'\n'
    (OUT/'bao_cao_tong_hop.md').write_text(md,encoding='utf-8')
    eq=build_doc(md)
    manifest={'status':'WAITING_REVIEW','G4':'PASS_I01_I15_2026-10-24','G5_complete':False,'base_commit':'a2021a9f591c56222f5ae16e169f278bf3cec5a7','executed_candidate':'4546d5bbd8f9130a420518b77dc3ad894bc7f42b','p1_reviewed_head':'d018921be66b12dc275933e1de9c2e755b74241a','p1_chapters_merge':'03d9bc9932f7919c5eb5d04075f0235a1e0448fc','p1_g4_updates':'Preserved local edits accepted by coordinator; SHA256 below','p2_reviewed_head':'f090eff8b5a58242f8391469772cb3bd329f43f4','p2_merge':'a2021a9f591c56222f5ae16e169f278bf3cec5a7','sources':{p.relative_to(ROOT).as_posix():sha(p) for p in SOURCES},'external_reference_mapping':REFMAP,'significant_edits':EDITS,'formula_count':eq,'presentation':'A4, Times New Roman 12pt, line spacing 1.15, group layout choice; no official template supplied','missing_cover_information':['School','Faculty','Instructor','Student names and IDs','Class/group'],'runtime_rerun':False}
    (OUT/'editorial_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'docx':str(OUT/'bao_cao_tong_hop.docx'),'formula_count':eq,'edits':len(EDITS)},ensure_ascii=False))
if __name__=='__main__':main()
