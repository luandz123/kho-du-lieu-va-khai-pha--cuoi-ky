// Dựng slide trình bày bản nâng cấp (5 phút). Chạy từ thư mục gốc repo:
//   NODE_PATH=<thư mục có node_modules pptxgenjs> node docs/slides/build_slides.js
// Ra: docs/slides/movie_platform_nang_cap.pptx
const path = require("path");
const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const fa = require("react-icons/fa");

const ROOT = path.resolve(__dirname, "..", "..");
const FIG = (p) => path.join(ROOT, "docs", "report", "figures", p);
const OUT = path.join(__dirname, "movie_platform_nang_cap.pptx");
const SKILL_THEME = process.env.APPLY_THEME;   // đường dẫn scripts/apply_theme.js

const THEME = {
  name: "PTIT Movie Platform",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1F2937", lt1: "FFFFFF", dk2: "7F1D1D", lt2: "F4F4F5",
    accent1: "B91C1C", accent2: "F59E0B", accent3: "0F766E", accent4: "64748B",
    accent5: "2563EB", accent6: "7C3AED", hlink: "2563EB", folHlink: "7C3AED",
  },
};
const HEX = THEME.colors;

async function icon(Comp, color, size = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(Comp, { color: "#" + color, size }));
  const png = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + png.toString("base64");
}

(async () => {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE";            // 13.333 x 7.5 in
  pres.title = "Movie Platform – bản nâng cấp";
  pres.author = "Nhóm Luân – Hùng";
  pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
  const C = pres.SchemeColor;
  const W = 13.333;

  // ------------------------------------------------------------ layouts
  pres.defineSlideMaster({
    title: "TITLE_DARK",
    background: { color: "1F2937" },
    objects: [
      { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 2.6, w: 11.7, h: 1.5, fontFace: THEME.headFontFace,
        fontSize: 36, bold: true, color: C.background1, align: "center", valign: "middle" }, text: "" } },
    ],
  });
  pres.defineSlideMaster({
    title: "CONTENT",
    background: { color: "FFFFFF" },
    margin: [0.5, 0.6, 0.6, 0.6],
    objects: [
      { placeholder: { options: { name: "kicker", type: "body", x: 0.6, y: 0.35, w: 9, h: 0.35, fontFace: THEME.bodyFontFace,
        fontSize: 13, bold: true, color: C.accent1, charSpacing: 2, margin: 0 }, text: "" } },
      { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.7, w: 12.1, h: 0.85, fontFace: THEME.headFontFace,
        fontSize: 28, bold: true, color: C.text1, margin: 0, valign: "middle", align: "left" }, text: "" } },
      { text: { text: "Movie Platform · bản nâng cấp · Kho dữ liệu và Khai phá dữ liệu", options: { x: 0.6, y: 7.0, w: 8, h: 0.3,
        fontFace: THEME.bodyFontFace, fontSize: 10, color: C.accent4, margin: 0 } } },
    ],
    slideNumber: { x: 12.1, y: 7.0, w: 0.6, h: 0.3, fontFace: THEME.bodyFontFace, fontSize: 10, color: C.accent4, align: "right" },
  });

  const sec = (t) => pres.addSection({ title: t });
  const slide = (sectionTitle, kicker, title) => {
    const s = pres.addSlide({ masterName: "CONTENT", sectionTitle });
    s.addText(kicker, { placeholder: "kicker" });
    s.addText(title, { placeholder: "title" });
    return s;
  };
  const card = (s, x, y, w, h, name, fill = C.background2) =>
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.08, fill: { color: fill }, line: { color: fill },
      objectName: name });
  const img = (s, p, x, y, w, h, name, alt) =>
    s.addImage({ path: p, x, y, w, h, objectName: name, altText: alt,
      shadow: { type: "outer", color: "000000", opacity: 0.18, blur: 6, offset: 2, angle: 90 } });

  const IC = {
    check: await icon(fa.FaCheck, HEX.lt1), file: await icon(fa.FaFileAlt, HEX.lt1), api: await icon(fa.FaPlug, HEX.lt1),
    cdc: await icon(fa.FaDatabase, HEX.lt1), stream: await icon(fa.FaStream, HEX.lt1), times: await icon(fa.FaTimes, HEX.lt1),
  };
  const dot = (s, x, y, d, ic, color, name) => {
    s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color }, line: { color }, objectName: name + " nền" });
    s.addImage({ data: ic, x: x + d * 0.25, y: y + d * 0.25, w: d * 0.5, h: d * 0.5, objectName: name, altText: name });
  };

  // ------------------------------------------------------------ 1. bìa
  sec("Mở đầu");
  {
    const s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Mở đầu" });
    s.addText([{ text: "HỌC VIỆN CÔNG NGHỆ BƯU CHÍNH VIỄN THÔNG", options: { breakLine: true } },
      { text: "VIỆN KHOA HỌC KỸ THUẬT BƯU ĐIỆN" }],
    { x: 0.8, y: 0.45, w: 11.7, h: 0.75, align: "center", fontSize: 14, bold: true, color: C.background2, isTextBox: true, charSpacing: 1 });
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 5.45, y: 1.3, w: 2.43, h: 1.05, rectRadius: 0.1, fill: { color: "FFFFFF" },
      line: { color: "FFFFFF" }, objectName: "Nền logo" });
    s.addImage({ path: FIG("logo_ptit.png"), x: 5.6, y: 1.38, w: 0.9, h: 0.9, sizing: { type: "contain", w: 0.9, h: 0.9 },
      objectName: "Logo PTIT", altText: "Logo Học viện Công nghệ Bưu chính Viễn thông" });
    s.addImage({ path: FIG("logo_ript.png"), x: 6.83, y: 1.38, w: 0.9, h: 0.9, sizing: { type: "contain", w: 0.9, h: 0.9 },
      objectName: "Logo RIPT", altText: "Logo Viện Khoa học Kỹ thuật Bưu điện" });
    s.addText("Movie Platform: nền tảng dữ liệu nhiều nguồn gần thời gian thực",
      { placeholder: "title" });
    s.addText("BẢN NÂNG CẤP · KHO DỮ LIỆU VÀ KHAI PHÁ DỮ LIỆU · MOVIELENS 1M", { x: 0.8, y: 4.25, w: 11.7, h: 0.4,
      align: "center", fontSize: 14, bold: true, color: C.accent2, charSpacing: 2, isTextBox: true });
    s.addText([
      { text: "Giảng viên: ", options: { bold: true } }, { text: "Phan Lý Huỳnh", options: { breakLine: true } },
      { text: "Sinh viên: ", options: { bold: true } }, { text: "Nguyễn Văn Luân – B23DCCC106 · Vũ Văn Hùng – B23DCCC078" },
    ], { x: 0.8, y: 5.05, w: 11.7, h: 0.8, align: "center", fontSize: 16, color: C.background1, isTextBox: true, paraSpaceAfter: 4 });
    s.addText("Hà Nội, 11/2026", { x: 0.8, y: 6.5, w: 11.7, h: 0.35, align: "center", fontSize: 12, color: C.background2, isTextBox: true });
    s.addNotes("Chào thầy. Nhóm em trình bày phần nâng cấp so với bản đã bảo vệ. Theo yêu cầu của thầy, em chỉ trình bày những điểm mới và khác biệt: kiến trúc mới, CDC, data lake, kho nạp tăng dần, Airflow và phần AI, kèm demo chạy thật.");
  }

  // ------------------------------------------------------------ 2. góp ý -> bản mới
  {
    const s = slide("Mở đầu", "THẦY GÓP Ý → BẢN MỚI", "Bản mới sửa đúng bốn điểm thầy đã góp ý");
    const rows = [
      ["Chỉ 1 nguồn, tệp tĩnh 2000–2003", "7 nguồn, 4 kiểu nạp: tệp, API, CDC, streaming"],
      ["Không có data lake", "MinIO chuẩn S3, ba tầng bronze → silver → gold"],
      ["Không có CDC", "Debezium đọc WAL của Postgres → Kafka → lake"],
      ["Demo chỉ trên terminal", "App web, Airflow, dashboard tự làm mới 60 giây"],
    ];
    s.addText("Thầy góp ý", { x: 0.6, y: 1.75, w: 4.6, h: 0.35, fontSize: 14, bold: true, color: C.accent4, margin: 0, isTextBox: true });
    s.addText("Bản nâng cấp", { x: 5.95, y: 1.75, w: 6.7, h: 0.35, fontSize: 14, bold: true, color: C.accent3, margin: 0, isTextBox: true });
    rows.forEach(([a, b], i) => {
      const y = 2.2 + i * 0.86;
      card(s, 0.6, y, 4.6, 0.72, `Góp ý ${i + 1}`);
      dot(s, 0.75, y + 0.16, 0.4, IC.times, HEX.accent4, `Biểu tượng thiếu ${i + 1}`);
      s.addText(a, { x: 1.3, y, w: 3.8, h: 0.72, fontSize: 16, color: C.text1, valign: "middle", margin: 0, isTextBox: true });
      s.addShape(pres.shapes.RIGHT_ARROW, { x: 5.35, y: y + 0.22, w: 0.45, h: 0.28, fill: { color: HEX.accent1 }, line: { color: HEX.accent1 },
        objectName: `Mũi tên ${i + 1}` });
      card(s, 5.95, y, 6.75, 0.72, `Bản mới ${i + 1}`, "E6F4F1");
      dot(s, 6.1, y + 0.16, 0.4, IC.check, HEX.accent3, `Biểu tượng đạt ${i + 1}`);
      s.addText(b, { x: 6.65, y, w: 5.95, h: 0.72, fontSize: 16, bold: true, color: C.text1, valign: "middle", margin: 0, isTextBox: true });
    });
    s.addText([{ text: "Làm thêm: ", options: { bold: true, color: C.accent1 } },
      { text: "nạp kho tăng dần · SCD loại 2 · 9 kiểm tra chất lượng · Airflow 3 DAG · gợi ý lai và tìm phim bằng tiếng Việt" }],
    { x: 0.6, y: 5.85, w: 12.1, h: 0.5, fontSize: 15, color: C.text1, margin: 0, isTextBox: true });
    s.addNotes("Buổi trước thầy góp ý bốn điểm: chỉ có một nguồn tĩnh, không có data lake, không có CDC, demo chỉ chạy trên terminal. Bản mới sửa đúng bốn điểm đó. Phần làm thêm là nạp kho tăng dần, SCD loại 2, kiểm tra chất lượng, điều phối bằng Airflow và gợi ý lai. (~30 giây)");
  }

  // ------------------------------------------------------------ 3. kiến trúc
  sec("Kiến trúc");
  {
    const s = slide("Kiến trúc", "KIẾN TRÚC", "Dữ liệu đi từ bảy nguồn qua data lake tới kho và ứng dụng");
    img(s, path.join(ROOT, "docs", "movie_platform_dataflow.png"), 0.95, 1.7, 9.48, 5.4, "Sơ đồ luồng dữ liệu",
      "Sơ đồ năm cột: nguồn, nạp (Airflow, Kafka, consumer), data lake MinIO ba tầng, kho Postgres + pgvector, Superset và app");
    const steps = [["1", "Nguồn", "tệp, API, CDC, streaming"], ["2", "Nạp", "Airflow theo lịch; Kafka cho CDC, streaming"],
      ["3", "Data lake", "MinIO · DuckDB · Parquet"], ["4", "Kho", "Postgres, lược đồ sao, pgvector"], ["5", "Khai thác", "Superset, app Streamlit"]];
    steps.forEach(([n, t, d], i) => {
      const y = 1.75 + i * 1.03;
      s.addShape(pres.shapes.OVAL, { x: 10.75, y, w: 0.45, h: 0.45, fill: { color: HEX.accent1 }, line: { color: HEX.accent1 }, objectName: `Số ${n}` });
      s.addText(n, { x: 10.75, y, w: 0.45, h: 0.45, align: "center", valign: "middle", fontSize: 14, bold: true, color: C.background1, margin: 0, isTextBox: true });
      s.addText([{ text: t, options: { bold: true, breakLine: true, fontSize: 15 } }, { text: d, options: { fontSize: 12, color: C.accent4 } }],
        { x: 11.3, y: y - 0.05, w: 1.75, h: 0.9, valign: "top", margin: 0, color: C.text1, isTextBox: true });
    });
    s.addNotes("Hệ thống chia năm cột. Nguồn gồm bốn kiểu nạp. Dữ liệu batch do Airflow lấy theo lịch; CDC và streaming đi qua Kafka rồi consumer ghi xuống lake. Data lake trên MinIO chia ba tầng, xử lý bằng DuckDB. Kho Postgres theo lược đồ sao, có pgvector. Khai thác bằng Superset và app Streamlit. Tất cả chạy bằng một file docker-compose. (~30 giây)");
  }

  // ------------------------------------------------------------ 4. nguồn
  {
    const s = slide("Kiến trúc", "NGUỒN DỮ LIỆU", "Bảy nguồn, bốn kiểu nạp, nhịp cập nhật khác nhau");
    const kinds = [
      [IC.file, HEX.accent5, "Tệp", "MovieLens 1M (1 lần)\nIMDb datasets (hằng ngày)"],
      [IC.api, HEX.accent3, "API", "Wikidata (SPARQL)\nWikipedia Pageviews (hằng ngày)\nWikipedia tóm tắt + poster"],
      [IC.cdc, HEX.accent1, "CDC", "Postgres của app xem phim\nbắt cả thêm, sửa, xóa"],
      [IC.stream, HEX.accent6, "Streaming", "Wikimedia EventStreams\n1–3 lần sửa bài mỗi giây"],
    ];
    kinds.forEach(([ic, col, t, d], i) => {
      const x = 0.6 + i * 2.25;
      card(s, x, 1.85, 2.05, 3.3, `Thẻ ${t}`);
      dot(s, x + 0.7, 2.05, 0.65, ic, col, `Biểu tượng ${t}`);
      s.addText(t, { x: x + 0.1, y: 2.8, w: 1.85, h: 0.45, align: "center", fontSize: 18, bold: true, color: C.text1, margin: 0, isTextBox: true });
      s.addText(d, { x: x + 0.15, y: 3.3, w: 1.75, h: 1.7, fontSize: 13, color: C.text1, valign: "top", margin: 0, isTextBox: true, paraSpaceAfter: 4 });
    });
    card(s, 9.75, 1.85, 2.95, 3.3, "Thẻ ghép phim", "FEF3C7");
    s.addText("98%", { x: 9.85, y: 2.0, w: 2.75, h: 1.0, align: "center", fontFace: THEME.headFontFace, fontSize: 54, bold: true, color: C.accent1, margin: 0, isTextBox: true });
    s.addText("phim MovieLens ghép được với IMDb", { x: 9.9, y: 3.0, w: 2.65, h: 0.6, align: "center", fontSize: 14, bold: true, color: C.text1, margin: 0, isTextBox: true });
    s.addText("2.949 qua links.csv\n857 qua tên chuẩn hóa + năm (±1)\n77 để trống, không đoán", { x: 9.95, y: 3.65, w: 2.6, h: 1.3, align: "center",
      fontSize: 12, color: C.text1, margin: 0, isTextBox: true });
    s.addText("Wikipedia giới hạn 10 request/phút: gọi tuần tự, chờ đúng Retry-After khi bị 429 · TMDB bị chặn tại Việt Nam nên thay bằng Wikipedia và IMDb",
      { x: 0.6, y: 5.45, w: 12.1, h: 0.6, fontSize: 13, color: C.accent4, margin: 0, isTextBox: true });
    s.addNotes("Bảy nguồn khác nhau cả định dạng lẫn nhịp cập nhật: IMDb cập nhật điểm mỗi ngày nên mỗi ngày chụp một bản; Wikipedia cho biết phim nào đang được quan tâm; app xem phim là nguồn sống. Khó nhất là ghép MovieLens với IMDb vì không có khóa chung: bước 1 dùng links.csv được 2.949 phim, bước 2 chuẩn hóa tên và ghép theo tên + năm được thêm 857, tổng 98%; 77 phim để trống vì ghép sai tệ hơn thiếu. (~30 giây)");
  }

  // ------------------------------------------------------------ 5. CDC
  sec("Pipeline");
  {
    const s = slide("Pipeline", "CDC · KAFKA", "Debezium đọc WAL của Postgres, app không gửi gì sang Kafka");
    img(s, FIG("nang_cap/kafka_json.jpg"), 0.6, 1.75, 6.4, 4.0, "Ảnh message Kafka", "Message Debezium: before null, after là dòng rating mới, source.lsn, op = c");
    const pts = [
      ["op = c / u / d", "thêm, sửa, xóa; before và after là dòng trước, sau thay đổi"],
      ["source.lsn", "vị trí trong WAL: sắp đúng thứ tự, loại bản trùng ở silver"],
      ["wal_level = logical", "publication + replication slot: Debezium tắt rồi bật vẫn đọc tiếp đúng chỗ"],
      ["Commit offset sau khi ghi", "consumer gom 500 message / 10 giây, ghi lake xong mới commit: at-least-once, không mất"],
    ];
    pts.forEach(([t, d], i) => {
      const y = 1.75 + i * 1.02;
      card(s, 7.35, y, 5.35, 0.88, `Ý CDC ${i + 1}`);
      s.addText([{ text: t, options: { bold: true, color: C.accent1, breakLine: true } }, { text: d }],
        { x: 7.5, y: y + 0.05, w: 5.1, h: 0.78, fontSize: 13.5, color: C.text1, valign: "middle", margin: 0, isTextBox: true });
    });
    s.addText("4 topic × 3 partition, giữ 72 giờ: app.public.ratings · app.public.users · wiki.recentchange · wiki.movie_edits",
      { x: 0.6, y: 6.0, w: 12.1, h: 0.4, fontSize: 13, color: C.accent4, margin: 0, isTextBox: true });
    s.addNotes("Mỗi thao tác trên app chỉ là một lệnh INSERT vào Postgres của app. Debezium đọc WAL, nhật ký Postgres vốn phải ghi, nên không quét bảng, bắt được cả DELETE và giữ đúng thứ tự theo LSN. Message có op, before, after. Consumer chỉ commit offset sau khi đã ghi file xuống lake; chết giữa chừng thì đọc lại, có thể trùng nhưng không mất, bản trùng được loại ở silver. (~35 giây)");
  }

  // ------------------------------------------------------------ 6. lake
  {
    const s = slide("Pipeline", "DATA LAKE", "Data lake ba tầng giữ dữ liệu thô để có thể xử lý lại");
    img(s, FIG("nang_cap/minio_bronze.jpg"), 0.6, 1.75, 6.4, 4.0, "Ảnh MinIO bronze", "Thư mục bronze/app_cdc/ratings, tệp JSONL mới nhất lúc 15:49");
    const tiers = [["BRONZE", "B45309", "FEF3C7", "Thô, đúng như nguồn: DAT, CSV, TSV.gz, JSONL; chia theo ingest_date"],
      ["SILVER", "475569", "E2E8F0", "Làm sạch, ép kiểu; giữ bản mới nhất theo LSN; op = d → is_deleted; ghép các nguồn"],
      ["GOLD", "A16207", "FEF9C3", "Đúng hình dạng kho (dim_*, fact_*), kèm changed_at để nạp tăng dần"]];
    tiers.forEach(([t, col, fill, d], i) => {
      const y = 1.75 + i * 1.33;
      card(s, 7.35, y, 5.35, 1.17, `Tầng ${t}`, fill);
      s.addText([{ text: t, options: { bold: true, color: col, breakLine: true, fontSize: 15 } }, { text: d, options: { fontSize: 13.5 } }],
        { x: 7.55, y: y + 0.05, w: 5.0, h: 1.07, color: C.text1, valign: "middle", margin: 0, isTextBox: true });
    });
    s.addText("DuckDB đọc ghi Parquet trực tiếp trên S3 · tệp rating 23 MB → 6 MB Parquet · các bước idempotent nên Airflow thử lại an toàn",
      { x: 0.6, y: 6.0, w: 12.1, h: 0.4, fontSize: 13, color: C.accent4, margin: 0, isTextBox: true });
    s.addNotes("MinIO tương thích S3. Tầng bronze giữ dữ liệu thô, file vừa xuất hiện là micro-batch chứa rating vừa chấm. Giữ bronze để khi phát hiện lỗi logic ở silver, gold thì xử lý lại được mà không cần lấy lại từ nguồn, vì sự kiện CDC đã qua không lấy lại được. Silver chỉ giữ bản mới nhất mỗi cặp theo LSN; gold đưa về đúng hình dạng kho. (~30 giây)");
  }

  // ------------------------------------------------------------ 7. kho
  {
    const s = slide("Pipeline", "KHO DỮ LIỆU", "Kho nạp tăng dần, giữ lịch sử người dùng theo SCD loại 2");
    img(s, FIG("nang_cap/luoc_do_sao_moi.png"), 0.6, 1.7, 6.6, 4.16, "Lược đồ sao mới",
      "Lược đồ sao: fact_rating, 2 bảng snapshot ngày, fact_wiki_edit; dim_user SCD2, dim_movie SCD1, movie_embedding");
    const pts = [
      ["Watermark − 1 giờ", "chỉ đọc thay đổi mới hơn mốc; đọc lùi 1 giờ để không sót sự kiện đến muộn"],
      ["Upsert khi bản mới hơn", "ON CONFLICT … WHERE changed_at mới hơn; chạy lại không nhân đôi; watermark cùng transaction"],
      ["SCD loại 2", "đổi nghề → đóng phiên bản cũ, thêm phiên bản mới; rating gắn phiên bản tại lúc chấm"],
      ["9 kiểm tra chất lượng", "SCD không chồng lấn, đối soát gold ↔ kho, độ tươi; sai 1 cái → task đỏ"],
    ];
    pts.forEach(([t, d], i) => {
      const y = 1.7 + i * 1.04;
      card(s, 7.5, y, 5.2, 0.9, `Ý kho ${i + 1}`);
      s.addText([{ text: t, options: { bold: true, color: C.accent1, breakLine: true } }, { text: d }],
        { x: 7.65, y: y + 0.04, w: 4.95, h: 0.82, fontSize: 13, color: C.text1, valign: "middle", margin: 0, isTextBox: true });
    });
    s.addText("4 bảng fact: rating (1.000.277 dòng) · điểm IMDb theo ngày (11.400) · lượt xem Wikipedia theo ngày (45.988) · sửa bài Wikipedia (147)",
      { x: 0.6, y: 6.05, w: 12.1, h: 0.4, fontSize: 13, color: C.accent4, margin: 0, isTextBox: true });
    s.addNotes("Bản cũ xóa sạch rồi nạp lại một triệu dòng; bản mới nạp tăng dần: bảng watermark lưu mốc đã nạp, mỗi lần chỉ đọc dòng mới hơn mốc trừ một giờ, ghi bằng INSERT ON CONFLICT chỉ khi bản mới hơn, nên chạy lại bao nhiêu lần cũng không nhân đôi. Lần đầu 2 phút, các lần sau vài giây. dim_user giữ lịch sử theo SCD loại 2. Cuối mỗi lần chạy có 9 kiểm tra chất lượng. (~35 giây)");
  }

  // ------------------------------------------------------------ 8. đầu cuối 40 giây
  sec("Kết quả");
  {
    const s = slide("Kết quả", "KIỂM CHỨNG ĐẦU – CUỐI", "Một lượt chấm điểm trên app nằm trong kho sau 40 giây");
    const steps = [["15:49:00", "Postgres app", "user 6050 chấm 5★ Toy Story 2"], ["15:49:01", "Kafka", "Debezium đọc WAL · op = c · offset 28"],
      ["15:49:03", "MinIO bronze", "tệp micro-batch JSONL"], ["15:49:25", "Airflow", "movie_incremental · 4/4 task xanh"],
      ["15:49:40", "Kho dữ liệu", "dw.fact_rating · rating = 5"]];
    s.addShape(pres.shapes.LINE, { x: 1.62, y: 1.95, w: 0, h: 4.0, line: { color: HEX.accent1, width: 2 }, objectName: "Trục thời gian" });
    steps.forEach(([t, n, d], i) => {
      const y = 1.75 + i * 0.98;
      s.addShape(pres.shapes.OVAL, { x: 1.47, y: y + 0.12, w: 0.3, h: 0.3, fill: { color: i === 4 ? HEX.accent3 : HEX.accent1 },
        line: { color: "FFFFFF", width: 2 }, objectName: `Mốc ${i + 1}` });
      s.addText(t, { x: 0.3, y: y + 0.05, w: 1.1, h: 0.42, fontSize: 13, bold: true, color: C.accent1, margin: 0, isTextBox: true, fontFace: "Consolas" });
      s.addText([{ text: n, options: { bold: true, breakLine: true } }, { text: d, options: { fontSize: 12.5, color: C.accent4 } }],
        { x: 1.95, y, w: 4.4, h: 0.8, fontSize: 15, color: C.text1, margin: 0, valign: "top", isTextBox: true });
    });
    img(s, FIG("nang_cap/app_pipeline.jpg"), 6.55, 1.7, 6.15, 3.84, "Ảnh panel hành trình", "Panel hành trình trên app: 5 chặng đều tích xanh, thay đổi đã vào kho sau 40 giây");
    s.addText("Gợi ý đổi theo: trước chấm là phim phổ biến, sau khi chấm 2 phim hoạt hình là A Bug's Life, Aladdin, Babe…",
      { x: 6.55, y: 5.7, w: 6.15, h: 0.65, fontSize: 13.5, color: C.text1, margin: 0, isTextBox: true });
    s.addNotes("Đây là demo chính, em sẽ chạy trực tiếp: tạo người dùng mới, chấm 5 sao Toy Story và Toy Story 2. Panel bên phải theo dõi thay đổi qua từng chặng kèm thời điểm: Postgres, Kafka sau 1 giây, MinIO sau 3 giây, bấm chạy pipeline thì Airflow chạy 4 bước, và 40 giây sau rating đã nằm trong kho. Gợi ý cho người dùng đổi từ phim phổ biến sang phim hoạt hình. Xóa rating thì kho đánh dấu is_deleted, đổi nghề thì dim_user thêm phiên bản. (~40 giây, kèm demo)");
  }

  // ------------------------------------------------------------ 9. Airflow + Superset
  {
    const s = slide("Kết quả", "ĐIỀU PHỐI · DASHBOARD", "Airflow điều phối, Superset hiển thị dữ liệu mới mỗi 60 giây");
    img(s, FIG("nang_cap/airflow_grid.jpg"), 0.6, 1.75, 5.9, 3.69, "Ảnh Airflow", "Airflow DAG movie_incremental, các lần chạy đều xanh");
    img(s, FIG("nang_cap/superset_1.jpg"), 6.8, 1.75, 5.9, 3.69, "Ảnh Superset", "Dashboard Superset thời gian thực");
    s.addText([{ text: "3 DAG: ", options: { bold: true } }, { text: "movie_incremental mỗi 15 phút (CDC, streaming), movie_daily 8:00 (IMDb, pageviews), movie_bootstrap chạy tay · retries = 2, max_active_runs = 1" }],
      { x: 0.6, y: 5.6, w: 5.9, h: 0.9, fontSize: 13, color: C.text1, margin: 0, valign: "top", isTextBox: true });
    s.addText([{ text: "8 biểu đồ, tài khoản chỉ đọc: ", options: { bold: true } }, { text: "rating mới qua CDC, phim đang được quan tâm (pageviews), MovieLens so với IMDb, lịch sử SCD2, giám sát pipeline" }],
      { x: 6.8, y: 5.6, w: 5.9, h: 0.9, fontSize: 13, color: C.text1, margin: 0, valign: "top", isTextBox: true });
    s.addNotes("Airflow có ba DAG; mỗi task gọi đúng một lệnh Python, việc nặng do DuckDB và Postgres làm. Nút trong app gọi REST API của Airflow. Dashboard mới đọc thẳng từ kho bằng tài khoản chỉ đọc, tự làm mới mỗi 60 giây: có rating mới từ app, phim đang hot theo lượt xem Wikipedia, ví dụ Home Alone tăng gần Giáng sinh, và chênh lệch điểm MovieLens với IMDb. (~30 giây)");
  }

  // ------------------------------------------------------------ 10. AI
  {
    const s = slide("Kết quả", "KHAI PHÁ · AI", "Tìm phim bằng câu tiếng Việt, nội dung phim vượt baseline");
    img(s, FIG("nang_cap/tim_phim_jaws.jpg"), 0.6, 1.75, 6.1, 3.81, "Ảnh tìm phim", "Gõ 'phim kinh dị về cá mập', kết quả đầu tiên là Jaws");
    s.addText("multilingual-e5-small → vector 384 chiều, lưu bằng pgvector (HNSW). Câu tiếng Việt vẫn tìm ra Jaws dù mô tả viết bằng tiếng Anh.",
      { x: 0.6, y: 5.7, w: 6.1, h: 0.7, fontSize: 13, color: C.text1, margin: 0, isTextBox: true });
    s.addChart(pres.charts.BAR, [{ name: "Precision@5", labels: ["Popularity", "CF (bản cũ)", "Chỉ nội dung", "Lai α = 0,9"],
      values: [0.2017, 0.2310, 0.2175, 0.2314] }], {
      x: 7.0, y: 1.7, w: 5.7, h: 3.9, barDir: "col", showTitle: true, title: "Precision@5 trên tập test (1.154 người dùng)",
      titleFontSize: 13, titleColor: HEX.dk1, titleFontFace: "+mn-lt", chartColors: [HEX.accent4, HEX.accent5, HEX.accent6, HEX.accent2],
      showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.0000", dataLabelFontSize: 11, dataLabelColor: HEX.dk1,
      dataLabelFontFace: "+mn-lt", valAxisMinVal: 0, valAxisMaxVal: 0.25, valAxisLabelFormatCode: "0.00", valAxisLabelFontSize: 10,
      catAxisLabelFontSize: 11, catAxisLabelColor: HEX.dk1, valAxisLabelColor: HEX.accent4, catAxisLabelFontFace: "+mn-lt",
      valAxisLabelFontFace: "+mn-lt", valGridLine: { color: "E5E7EB", size: 0.5 }, catGridLine: { style: "none" }, showLegend: false,
      objectName: "Biểu đồ Precision@5", altText: "Precision@5: Popularity 0,2017; CF 0,2310; chỉ nội dung 0,2175; lai 0,2314",
    });
    s.addText("Lai chỉ ngang CF (0,2314 so với 0,2310), nói thẳng như vậy. Giá trị nằm ở phim mới chưa ai chấm, tìm theo mô tả và giải thích lý do gợi ý.",
      { x: 7.0, y: 5.7, w: 5.7, h: 0.7, fontSize: 13, color: C.text1, margin: 0, isTextBox: true });
    s.addNotes("Mỗi phim được ghép thành đoạn văn gồm tên, thể loại, mô tả Wikipedia, đạo diễn, diễn viên; mô hình E5 đa ngôn ngữ biến thành vector 384 chiều lưu bằng pgvector. Gõ câu tiếng Việt, kho tìm vector gần nhất theo cosine. Đánh giá đúng giao thức bản cũ: chạy lại CF ra đúng 0,231. Hybrid chỉ ngang CF, em nói thật; nhưng chỉ dùng mô tả phim, không dùng hành vi ai, đã đạt 0,2175, vượt baseline phổ biến của bản cũ. Đó là giá trị của nguồn dữ liệu mới. (~35 giây)");
  }

  // ------------------------------------------------------------ 11. kết luận
  {
    const s = slide("Kết quả", "KẾT LUẬN", "Từ kho dữ liệu một nguồn thành nền tảng dữ liệu nhiều nguồn");
    const stats = [["7", "nguồn dữ liệu, 4 kiểu nạp"], ["40 giây", "từ lượt chấm trên app tới kho"], ["9", "kiểm tra chất lượng mỗi lần nạp"]];
    stats.forEach(([n, d], i) => {
      const x = 0.6 + i * 4.1;
      card(s, x, 1.85, 3.85, 1.9, `Chỉ số ${i + 1}`, i === 1 ? "FEE2E2" : C.background2);
      s.addText(n, { x, y: 1.95, w: 3.85, h: 1.05, align: "center", fontFace: THEME.headFontFace, fontSize: 48, bold: true, color: C.accent1, margin: 0, isTextBox: true });
      s.addText(d, { x: x + 0.2, y: 3.0, w: 3.45, h: 0.55, align: "center", fontSize: 15, color: C.text1, margin: 0, isTextBox: true });
    });
    s.addText("Hạn chế", { x: 0.6, y: 4.1, w: 5.9, h: 0.4, fontSize: 17, bold: true, color: C.text1, margin: 0, isTextBox: true });
    s.addText([
      { text: "Chạy trên một máy, chưa có sẵn sàng cao", options: { bullet: true, breakLine: true } },
      { text: "fact_rating giữ trạng thái hiện tại, chưa lưu mọi lần chấm lại", options: { bullet: true, breakLine: true } },
      { text: "Lai chưa vượt CF trên chỉ số offline", options: { bullet: true } },
    ], { x: 0.6, y: 4.55, w: 5.9, h: 1.6, fontSize: 14, color: C.text1, margin: 0, paraSpaceAfter: 6, valign: "top", isTextBox: true });
    s.addText("Hướng phát triển", { x: 6.8, y: 4.1, w: 5.9, h: 0.4, fontSize: 17, bold: true, color: C.text1, margin: 0, isTextBox: true });
    s.addText([
      { text: "Kafka nhiều broker, giám sát độ trễ replication slot", options: { bullet: true, breakLine: true } },
      { text: "Bảng sự kiện giao dịch lưu mọi sự kiện CDC", options: { bullet: true, breakLine: true } },
      { text: "Iceberg / Delta Lake cho tầng silver, gold", options: { bullet: true } },
    ], { x: 6.8, y: 4.55, w: 5.9, h: 1.6, fontSize: 14, color: C.text1, margin: 0, paraSpaceAfter: 6, valign: "top", isTextBox: true });
    s.addNotes("Tóm lại: bảy nguồn với bốn kiểu nạp, CDC bằng Debezium và Kafka, data lake ba tầng, kho nạp tăng dần có SCD loại 2 và chín kiểm tra chất lượng, Airflow điều phối, tìm phim bằng ngữ nghĩa. Hạn chế lớn nhất: chạy trên một máy, và nếu Debezium dừng lâu thì WAL tích lại, cần giám sát. (~20 giây)");
  }

  // ------------------------------------------------------------ 12. cảm ơn
  {
    const s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Kết quả" });
    s.addText("Em xin cảm ơn thầy đã lắng nghe", { placeholder: "title" });
    s.addText("Demo trực tiếp: app http://localhost:8501 · Kafka UI :8080 · MinIO :9001 · Airflow :8081 · Superset :8089",
      { x: 0.8, y: 4.3, w: 11.7, h: 0.5, align: "center", fontSize: 15, color: C.background2, isTextBox: true });
    s.addText("Video dự phòng có lồng tiếng: docs/demo/movie_platform_demo_longtieng.mp4 · github.com/luandz123/kho-du-lieu-va-khai-pha--cuoi-ky",
      { x: 0.8, y: 4.85, w: 11.7, h: 0.5, align: "center", fontSize: 13, color: C.background2, isTextBox: true });
    s.addNotes("Cảm ơn thầy, mời thầy đặt câu hỏi. Câu hay gặp: CDC khác đọc theo updated_at thế nào; consumer chết thì sao; vì sao cần bronze; watermark lùi 1 giờ để làm gì; SCD loại 2 ở đâu; hybrid có tốt hơn CF không. Đáp án chi tiết trong docs/demo/kich_ban_video.md.");
  }

  await pres.writeFile({ fileName: OUT });
  if (SKILL_THEME) {
    const { applyTheme } = require(SKILL_THEME);
    await applyTheme(OUT, THEME);
  }
  console.log("->", OUT);
})().catch((e) => { console.error(e); process.exit(1); });
