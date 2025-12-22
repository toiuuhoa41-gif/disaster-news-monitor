export const NEWS_SOURCES = [
  {
    id: "vnexpress",
    name: "VnExpress",
    domain: "vnexpress.net",
    status: "active",
    articlesCount: 156,
    lastCrawl: "2024-01-15T10:30:00Z",
    categories: ["Thời sự", "Dân sinh", "Giao thông"]
  },
  {
    id: "tuoitre",
    name: "Tuổi Trẻ",
    domain: "tuoitre.vn",
    status: "active",
    articlesCount: 89,
    lastCrawl: "2024-01-15T10:25:00Z",
    categories: ["Thời sự", "Xã hội"]
  },
  {
    id: "thanhnien",
    name: "Thanh Niên",
    domain: "thanhnien.vn",
    status: "active",
    articlesCount: 72,
    lastCrawl: "2024-01-15T10:28:00Z",
    categories: ["Thời sự", "Xã hội"]
  },
  {
    id: "dantri",
    name: "Dân Trí",
    domain: "dantri.com.vn",
    status: "active",
    articlesCount: 98,
    lastCrawl: "2024-01-15T10:22:00Z",
    categories: ["Thời sự"]
  },
  {
    id: "vietnamnet",
    name: "VietnamNet",
    domain: "vietnamnet.vn",
    status: "warning",
    articlesCount: 45,
    lastCrawl: "2024-01-15T09:15:00Z",
    categories: ["Thời sự"]
  },
  {
    id: "nld",
    name: "Người Lao Động",
    domain: "nld.com.vn",
    status: "active",
    articlesCount: 67,
    lastCrawl: "2024-01-15T10:20:00Z",
    categories: ["Thời sự"]
  },
  {
    id: "laodong",
    name: "Lao Động",
    domain: "laodong.vn",
    status: "error",
    articlesCount: 0,
    lastCrawl: "2024-01-15T08:00:00Z",
    categories: ["Thời sự"]
  },
  {
    id: "vtc",
    name: "VTC News",
    domain: "vtc.vn",
    status: "active",
    articlesCount: 54,
    lastCrawl: "2024-01-15T10:18:00Z",
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

export const RECENT_ARTICLES = [
  {
    id: 1,
    title: "Bão số 9 đổ bộ miền Trung với sức gió giật cấp 15",
    source: "VnExpress",
    category: "Thời sự",
    publishedAt: "2024-01-15T10:30:00Z",
    keywords: ["bão", "gió mạnh", "miền Trung"],
    severity: "high"
  },
  {
    id: 2,
    title: "Lũ quét cuốn trôi 5 ngôi nhà tại Lào Cai",
    source: "Tuổi Trẻ",
    category: "Thời sự",
    publishedAt: "2024-01-15T09:45:00Z",
    keywords: ["lũ quét", "sạt lở"],
    severity: "high"
  },
  {
    id: 3,
    title: "Cảnh báo mưa lớn diện rộng từ Nghệ An đến Thừa Thiên Huế",
    source: "Thanh Niên",
    category: "Dân sinh",
    publishedAt: "2024-01-15T09:20:00Z",
    keywords: ["mưa lớn", "cảnh báo"],
    severity: "medium"
  },
  {
    id: 4,
    title: "Sơ tán hàng nghìn hộ dân trước khi bão đổ bộ",
    source: "Dân Trí",
    category: "Xã hội",
    publishedAt: "2024-01-15T08:55:00Z",
    keywords: ["sơ tán", "bão"],
    severity: "medium"
  },
  {
    id: 5,
    title: "Động đất 4.5 độ richter tại Điện Biên",
    source: "VietnamNet",
    category: "Thời sự",
    publishedAt: "2024-01-15T08:30:00Z",
    keywords: ["động đất", "rung chấn"],
    severity: "medium"
  },
  {
    id: 6,
    title: "Hạn hán kéo dài, hàng trăm hecta lúa chết khô",
    source: "Người Lao Động",
    category: "Dân sinh",
    publishedAt: "2024-01-15T07:45:00Z",
    keywords: ["hạn hán", "khô hạn"],
    severity: "low"
  }
];

export const CRAWL_STATS = {
  totalArticles: 1247,
  disasterArticles: 381,
  todayArticles: 156,
  activeSources: 7,
  lastUpdate: "2024-01-15T10:30:00Z"
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
