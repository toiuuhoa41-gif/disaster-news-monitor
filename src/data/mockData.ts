export interface Article {
  url: string;
  source: string;
  category: string;
  title: string;
  authors: string[];
  publish_date: string;
  update_date: string;
  tags: string[];
  text: string;
  summary: string;
  keywords: string[];
  media: {
    top_image: string;
    images: string[];
    videos: string[];
  };
  language: string;
  severity?: "high" | "medium" | "low";
}

export interface NewsSource {
  id: string;
  name: string;
  domain: string;
  status: "active" | "warning" | "error";
  articlesCount: number;
  lastCrawl: string;
  categories: string[];
}

export const NEWS_SOURCES: NewsSource[] = [
  {
    id: "vnexpress",
    name: "VnExpress",
    domain: "vnexpress.net",
    status: "active",
    articlesCount: 156,
    lastCrawl: "2025-12-22T10:30:00+07:00",
    categories: ["Thời sự", "Dân sinh", "Giao thông"]
  },
  {
    id: "tuoitre",
    name: "Tuổi Trẻ",
    domain: "tuoitre.vn",
    status: "active",
    articlesCount: 89,
    lastCrawl: "2025-12-22T10:25:00+07:00",
    categories: ["Thời sự", "Xã hội"]
  },
  {
    id: "thanhnien",
    name: "Thanh Niên",
    domain: "thanhnien.vn",
    status: "active",
    articlesCount: 72,
    lastCrawl: "2025-12-22T10:28:00+07:00",
    categories: ["Thời sự", "Xã hội"]
  },
  {
    id: "dantri",
    name: "Dân Trí",
    domain: "dantri.com.vn",
    status: "active",
    articlesCount: 98,
    lastCrawl: "2025-12-22T10:22:00+07:00",
    categories: ["Thời sự"]
  },
  {
    id: "vietnamnet",
    name: "VietnamNet",
    domain: "vietnamnet.vn",
    status: "warning",
    articlesCount: 45,
    lastCrawl: "2025-12-22T09:15:00+07:00",
    categories: ["Thời sự"]
  },
  {
    id: "nld",
    name: "Người Lao Động",
    domain: "nld.com.vn",
    status: "active",
    articlesCount: 67,
    lastCrawl: "2025-12-22T10:20:00+07:00",
    categories: ["Thời sự"]
  },
  {
    id: "laodong",
    name: "Lao Động",
    domain: "laodong.vn",
    status: "error",
    articlesCount: 0,
    lastCrawl: "2025-12-22T08:00:00+07:00",
    categories: ["Thời sự"]
  },
  {
    id: "vtc",
    name: "VTC News",
    domain: "vtc.vn",
    status: "active",
    articlesCount: 54,
    lastCrawl: "2025-12-22T10:18:00+07:00",
    categories: ["Thời sự"]
  }
];

export const DISASTER_KEYWORDS = {
  weather: ["bão", "áp thấp nhiệt đới", "siêu bão", "gió mạnh", "mưa lớn", "mưa đá", "ngập úng", "triều cường"],
  flood: ["lũ", "lụt", "lũ quét", "sạt lở", "sạt lở đất", "lở núi", "vỡ đê"],
  drought: ["hạn hán", "nắng nóng", "khô hạn", "thiếu nước", "cháy rừng"],
  earthquake: ["động đất", "rung chấn", "chấn động", "sóng thần"],
  general: ["thiên tai", "thảm họa", "cứu hộ", "cứu nạn", "sơ tán", "di dời", "cảnh báo khẩn"]
};

export const RECENT_ARTICLES: Article[] = [
  {
    url: "https://vnexpress.net/mua-lu-lich-su-o-dak-lak-lam-113-nguoi-chet-4996033.html",
    source: "vnexpress.net",
    category: "Thời sự",
    title: "Mưa lũ lịch sử ở Đăk Lăk làm 113 người chết",
    authors: ["Bùi Toàn"],
    publish_date: "2025-12-19T22:28:25+07:00",
    update_date: "2025-12-19T22:28:25+07:00",
    tags: ["lũ lụt phú yên", "lũ lụt đăk lăk", "hòa thịnh"],
    text: "Đăk Lăk xác định 113 người tử vong trong đợt mưa lũ vừa qua, tăng gần gấp đôi so với thống kê ban đầu, Bộ Công an đang làm việc về việc xả lũ thủy điện Sông Ba Hạ.",
    summary: "Đăk Lăk xác định 113 người tử vong trong đợt mưa lũ vừa qua, tăng gần gấp đôi so với thống kê ban đầu.",
    keywords: ["mưa", "lũ", "lịch sử", "đăk lăk", "chết", "113"],
    media: {
      top_image: "https://i2-vnexpress.vnecdn.net/2025/12/19/4494450970605458454-1763815601-4926-4502-1766158002.webp?w=1200&h=0&q=100&dpr=1&fit=crop&s=IVfIj95ZVUUFhBNcrQDmRA",
      images: [],
      videos: []
    },
    language: "vi",
    severity: "high"
  },
  {
    url: "https://vnexpress.net/sat-lo-hang-nghin-met-bo-ke-ven-bien-quang-tri-4995836.html",
    source: "vnexpress.net",
    category: "Thời sự",
    title: "Sạt lở hàng nghìn mét bờ kè ven biển Quảng Trị",
    authors: [],
    publish_date: "2025-12-20T12:00:00+07:00",
    update_date: "2025-12-20T12:00:00+07:00",
    tags: ["tỉnh quảng trị", "sạt lở bờ biển", "kè biển"],
    text: "Hơn 100 m bờ biển tại bến cá thôn 6, xã Triệu Cơ bị nước biển khoét sâu vào đất liền gần 10 m. Bến cá bằng bêtông bị sóng đánh sập nhiều đoạn.",
    summary: "Sau các đợt mưa bão, sóng biển xâm thực làm sạt lở nhiều tuyến bờ kè ven biển Quảng Trị, cuốn trôi cây cối, công trình phụ trợ.",
    keywords: ["sạt lở", "bờ kè", "quảng trị", "biển", "mưa bão"],
    media: {
      top_image: "https://i2-vnexpress.vnecdn.net/2025/12/19/anh-4-1766126016-1766127036-1766157587-1766157609.jpg?w=1200&h=0&q=100&dpr=1&fit=crop&s=8j2kKYd6c9maPiVYie8-jQ",
      images: [],
      videos: []
    },
    language: "vi",
    severity: "high"
  },
  {
    url: "https://vnexpress.net/chay-nha-o-da-lat-4996389.html",
    source: "vnexpress.net",
    category: "Thời sự",
    title: "Nhà ở Đà Lạt cháy giữa đêm, 4 người được cứu",
    authors: [],
    publish_date: "2025-12-21T08:18:08+07:00",
    update_date: "2025-12-21T08:18:08+07:00",
    tags: ["đà lạt", "cháy nhà", "cứu nạn cứu hộ", "pccc", "lâm đồng"],
    text: "Căn nhà ở phường Xuân Hương - Đà Lạt bốc cháy trong đêm, khói lửa bao trùm khiến 4 người mắc kẹt, sáng 21/12.",
    summary: "Căn nhà ở phường Xuân Hương - Đà Lạt bốc cháy trong đêm, khói lửa bao trùm khiến 4 người mắc kẹt.",
    keywords: ["cháy", "đà lạt", "cứu hộ", "lửa", "cảnh sát"],
    media: {
      top_image: "https://i2-vnexpress.vnecdn.net/2025/12/21/chay-nha-da-lat-1766279123-183-2346-6761-1766280944.jpg?w=1200&h=0&q=100&dpr=1&fit=crop&s=JthvRQcO4EX70pgEmaRmaQ",
      images: [],
      videos: []
    },
    language: "vi",
    severity: "medium"
  },
  {
    url: "https://vnexpress.net/lien-hop-quoc-ho-tro-khan-cap-2-6-trieu-usd-cho-viet-nam-4995755.html",
    source: "vnexpress.net",
    category: "Thời sự",
    title: "Liên Hợp Quốc hỗ trợ khẩn cấp 2,6 triệu USD cho Việt Nam",
    authors: ["Gia Chính"],
    publish_date: "2025-12-19T11:43:47+07:00",
    update_date: "2025-12-19T11:43:47+07:00",
    tags: ["ứng phó", "liên hợp quốc", "hỗ trợ"],
    text: "Khoản hỗ trợ mới được công bố nâng tổng số tiền quốc tế hỗ trợ Việt Nam phòng chống thiên tai trong năm 2025 lên 23,5 triệu USD.",
    summary: "Khoản hỗ trợ mới được công bố nâng tổng số tiền quốc tế hỗ trợ Việt Nam phòng chống thiên tai trong năm 2025 lên 23,5 triệu USD.",
    keywords: ["hỗ trợ", "liên hợp quốc", "thiên tai", "việt nam", "usd"],
    media: {
      top_image: "https://i2-vnexpress.vnecdn.net/2025/12/19/img-2348-jpg-1766114913-176611-4995-6451-1766115322.jpg?w=1200&h=0&q=100&dpr=1&fit=crop&s=GWPY_J9i4Dr-jrI_MN8Hvg",
      images: [],
      videos: []
    },
    language: "vi",
    severity: "medium"
  },
  {
    url: "https://vnexpress.net/gan-18-ty-dong-hoi-sinh-truong-hoc-vung-lu-4995517.html",
    source: "vnexpress.net",
    category: "Thời sự",
    title: "Gần 18 tỷ đồng hồi sinh trường học vùng lũ",
    authors: ["Nga Thanh"],
    publish_date: "2025-12-19T08:06:46+07:00",
    update_date: "2025-12-19T08:06:46+07:00",
    tags: ["ánh sáng học đường", "quỹ hy vọng"],
    text: "Gần 20.000 học sinh tại 50 ngôi trường từ Bắc vào Nam đã có lớp học mới khang trang sau bão lũ, nhờ nguồn lực 18 tỷ đồng từ Quỹ Hy vọng và độc giả VnExpress.",
    summary: "Gần 20.000 học sinh tại 50 ngôi trường từ Bắc vào Nam đã có lớp học mới khang trang sau bão lũ.",
    keywords: ["trường học", "lũ", "hỗ trợ", "quỹ hy vọng", "bão"],
    media: {
      top_image: "https://i2-vnexpress.vnecdn.net/2025/12/18/a-nh-ma-n-hi-nh-2025-12-18-lu-4173-7685-1766050735.png?w=1200&h=0&q=100&dpr=1&fit=crop&s=TJ17X-jMJhICyfZSkEOoyg",
      images: [],
      videos: []
    },
    language: "vi",
    severity: "low"
  },
  {
    url: "https://vnexpress.net/loat-nha-chong-lu-o-hoa-thinh-sau-hon-hai-tuan-xay-dung-4996108.html",
    source: "vnexpress.net",
    category: "Thời sự",
    title: "Loạt nhà chống lũ ở Hòa Thịnh sau hơn hai tuần xây dựng",
    authors: [],
    publish_date: "2025-12-20T10:58:30+07:00",
    update_date: "2025-12-20T10:58:30+07:00",
    tags: ["đăk lăk", "nhà chống lũ", "hòa thịnh", "xây dựng"],
    text: "Sau hơn hai tuần thi công, phần lớn các căn nhà đã hoàn thành tầng một, khu vực gác lửng tầng hai đang dần hoàn thiện.",
    summary: "Sau hơn hai tuần thi công, phần lớn các căn nhà đã hoàn thành tầng một, khu vực gác lửng tầng hai đang dần hoàn thiện.",
    keywords: ["nhà chống lũ", "hòa thịnh", "xây dựng", "đăk lăk"],
    media: {
      top_image: "https://i2-vnexpress.vnecdn.net/2025/12/20/hinhhaicannha-21-1766210626.jpg?w=1200&h=0&q=100&dpr=1&fit=crop&s=axzQLoosytGz7Yr70_1B6Q",
      images: [],
      videos: []
    },
    language: "vi",
    severity: "low"
  }
];

export const CRAWL_STATS = {
  totalArticles: 1247,
  disasterArticles: 381,
  todayArticles: 156,
  activeSources: 7,
  lastUpdate: "2025-12-22T10:30:00+07:00"
};

export const HOURLY_STATS = [
  { hour: "00:00", articles: 12, disaster: 3 },
  { hour: "02:00", articles: 8, disaster: 2 },
  { hour: "04:00", articles: 5, disaster: 1 },
  { hour: "06:00", articles: 24, disaster: 8 },
  { hour: "08:00", articles: 45, disaster: 15 },
  { hour: "10:00", articles: 62, disaster: 24 },
  { hour: "12:00", articles: 38, disaster: 12 },
  { hour: "14:00", articles: 42, disaster: 14 },
  { hour: "16:00", articles: 35, disaster: 11 },
  { hour: "18:00", articles: 28, disaster: 9 },
  { hour: "20:00", articles: 22, disaster: 7 },
  { hour: "22:00", articles: 15, disaster: 4 },
];

export const CATEGORY_DISTRIBUTION = [
  { name: "Thời tiết", value: 145, color: "hsl(var(--chart-1))" },
  { name: "Lũ lụt", value: 98, color: "hsl(var(--chart-2))" },
  { name: "Hạn hán", value: 56, color: "hsl(var(--chart-3))" },
  { name: "Động đất", value: 42, color: "hsl(var(--chart-4))" },
  { name: "Khác", value: 40, color: "hsl(var(--chart-5))" },
];
