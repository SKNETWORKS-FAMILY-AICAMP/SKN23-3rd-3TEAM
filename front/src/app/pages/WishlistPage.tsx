import { useState } from "react";
import { Link } from "react-router";
import { Heart, Star } from "lucide-react";
import { motion } from "motion/react";

export const PRODUCTS = [
  {
    id: 1,
    name: "세라마이드 딥 모이스처 세럼",
    brand: "이니스프리",
    price: 28000,
    rating: 4.8,
    reviews: 1245,
    category: "세럼",
    image: "https://images.unsplash.com/photo-1688413467228-296b52dc4a34?w=400&h=400&fit=crop",
    tags: ["수분 부족", "건성", "복합성"],
    badge: "추천",
    badgeColor: "#84C13D",
    desc: "7중 히알루론산과 세라마이드로 피부 장벽을 강화하고 깊은 보습을 제공합니다.",
    liked: true,
  },
  {
    id: 2,
    name: "수분 크림 리치 텍스처",
    brand: "라네즈",
    price: 35000,
    rating: 4.7,
    reviews: 987,
    category: "크림",
    image: "https://images.unsplash.com/photo-1767611033962-6e3124c71450?w=400&h=400&fit=crop",
    tags: ["건성", "복합성"],
    badge: "인기",
    badgeColor: "#F59E0B",
    desc: "풍부한 크리미 텍스처로 건조한 피부에 집중적인 수분과 영양을 공급합니다.",
    liked: true,
  },
  {
    id: 3,
    name: "무기자차 선크림 SPF50+",
    brand: "코스알엑스",
    price: 22000,
    rating: 4.9,
    reviews: 2156,
    category: "선케어",
    image: "https://images.unsplash.com/photo-1709551264845-e9dddd775388?w=400&h=400&fit=crop",
    tags: ["민감성", "복합성", "지성"],
    badge: "NEW",
    badgeColor: "#3B82F6",
    desc: "순수 무기자차 성분으로 민감한 피부도 안심하고 사용할 수 있는 자외선 차단제.",
    liked: false,
  },
  {
    id: 4,
    name: "갈락토미세스 토닝 토너",
    brand: "스킨1004",
    price: 18000,
    rating: 4.6,
    reviews: 876,
    category: "토너",
    image: "https://images.unsplash.com/photo-1688413550763-f6edddd246a4?w=400&h=400&fit=crop",
    tags: ["모든 피부", "미백"],
    badge: "",
    badgeColor: "",
    desc: "갈락토미세스 발효 성분으로 피부 결을 고르게 하고 브라이트닝 효과를 선사합니다.",
    liked: true,
  },
  {
    id: 5,
    name: "아이 크림 리프팅 포뮬러",
    brand: "오휘",
    price: 45000,
    rating: 4.5,
    reviews: 543,
    category: "아이케어",
    image: "https://images.unsplash.com/photo-1664530964949-713a3cccad31?w=400&h=400&fit=crop",
    tags: ["탄력", "노화케어"],
    badge: "",
    badgeColor: "",
    desc: "눈가 탄력을 집중적으로 개선하는 리프팅 성분과 보습 성분이 조화로운 아이크림.",
    liked: false,
  },
];

const CATEGORIES = ["전체", "세럼", "크림", "토너", "선케어", "아이케어"];

export function WishlistPage() {
  const [likedProducts, setLikedProducts] = useState<Set<number>>(
    new Set(PRODUCTS.filter((p) => p.liked).map((p) => p.id))
  );
  const [selectedCategory, setSelectedCategory] = useState("전체");

  const toggleLike = (id: number, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setLikedProducts((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const filteredProducts = PRODUCTS.filter((p) => {
    return selectedCategory === "전체" || p.category === selectedCategory;
  });

  return (
    <div className="h-full overflow-y-auto bg-[#F8FBF3]">
      <div className="max-w-5xl mx-auto px-4 py-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-gray-900 font-bold">위시리스트</h1>
            <p className="text-sm text-gray-500 mt-0.5">AI가 추천한 내 피부 맞춤 제품</p>
          </div>
          <span
            className="px-3 py-1.5 rounded-xl text-sm font-semibold text-white"
            style={{ background: "#84C13D" }}
          >
            {likedProducts.size}개 저장됨
          </span>
        </div>

        {/* Category Filter */}
        <div className="flex gap-2 overflow-x-auto pb-2 mb-5 scrollbar-none">
          {CATEGORIES.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`flex-shrink-0 px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 ${
                selectedCategory === cat ? "text-white shadow-sm" : "bg-white text-gray-500 border border-gray-200 hover:border-[#84C13D]"
              }`}
              style={selectedCategory === cat ? { background: "linear-gradient(135deg, #84C13D, #6BA32E)" } : {}}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* Products Grid */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {filteredProducts.map((product, idx) => (
            <motion.div
              key={product.id}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: idx * 0.06 }}
            >
              <Link to={`/wishlist/${product.id}`} className="block group">
                <div className="bg-white rounded-2xl overflow-hidden border border-gray-100 shadow-sm hover:shadow-md transition-all duration-200 hover:-translate-y-1">
                  {/* Image */}
                  <div className="relative aspect-square overflow-hidden bg-gray-50">
                    <img
                      src={product.image}
                      alt={product.name}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                    />
                    {product.badge && (
                      <span
                        className="absolute top-2 left-2 text-[10px] font-bold px-2 py-0.5 rounded-lg text-white"
                        style={{ background: product.badgeColor }}
                      >
                        {product.badge}
                      </span>
                    )}
                    <button
                      onClick={(e) => toggleLike(product.id, e)}
                      className="absolute top-2 right-2 w-8 h-8 bg-white rounded-full flex items-center justify-center shadow-md transition-transform hover:scale-110"
                    >
                      <Heart
                        className="w-4 h-4 transition-colors"
                        style={{
                          color: likedProducts.has(product.id) ? "#EF4444" : "#D1D5DB",
                          fill: likedProducts.has(product.id) ? "#EF4444" : "none",
                        }}
                      />
                    </button>
                  </div>
                  {/* Info */}
                  <div className="p-3">
                    <p className="text-[11px] text-gray-400 mb-0.5">{product.brand}</p>
                    <p className="text-xs font-semibold text-gray-800 leading-tight mb-1.5 line-clamp-2">
                      {product.name}
                    </p>
                    <div className="flex items-center gap-1 mb-2">
                      <Star className="w-3 h-3 fill-yellow-400 text-yellow-400" />
                      <span className="text-[11px] font-semibold text-gray-700">{product.rating}</span>
                      <span className="text-[10px] text-gray-400">({product.reviews.toLocaleString()})</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-bold text-gray-900">
                        ₩{product.price.toLocaleString()}
                      </span>
                    </div>
                    <div className="flex flex-wrap gap-1 mt-2">
                      {product.tags.slice(0, 2).map((tag) => (
                        <span
                          key={tag}
                          className="text-[10px] px-1.5 py-0.5 rounded-md font-medium"
                          style={{ background: "#E8F5D0", color: "#4A7A1E" }}
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </Link>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
}