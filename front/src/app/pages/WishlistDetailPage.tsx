import { useState } from "react";
import { useParams, useNavigate } from "react-router";
import {
  ChevronLeft,
  Heart,
  Star,
  ShoppingBag,
  Bookmark,
  Share2,
  ChevronDown,
  Check,
  Truck,
  RotateCcw,
  Shield,
} from "lucide-react";
import { motion } from "motion/react";
import { PRODUCTS } from "./WishlistPage";

const REVIEWS = [
  { id: 1, author: "피부고민**", rating: 5, content: "복합성 피부인데 정말 잘 맞아요. 수분감도 오래가고 끈적임 없이 촉촉해요!", date: "2025.02.20", helpful: 42 },
  { id: 2, author: "건성피부**", rating: 5, content: "예민한 피부도 자극 없이 사용 가능해요. 향도 은은하고 좋아요.", date: "2025.02.18", helpful: 28 },
  { id: 3, author: "서울거주**", rating: 4, content: "발림성이 좋고 빠른 흡수가 마음에 들어요. 재구매 의사 있습니다!", date: "2025.02.15", helpful: 15 },
];

export function WishlistDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const product = PRODUCTS.find((p) => p.id === Number(id));
  const [isLiked, setIsLiked] = useState(product?.liked ?? false);
  const [savedToWishlist, setSavedToWishlist] = useState(false);
  const [purchaseSuccess, setPurchaseSuccess] = useState(false);
  const [expandedSection, setExpandedSection] = useState<string | null>("desc");

  if (!product) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <p className="text-gray-500 font-medium">제품을 찾을 수 없습니다</p>
          <button
            onClick={() => navigate("/wishlist")}
            className="mt-3 text-sm text-[#84C13D] hover:underline"
          >
            위시리스트로 돌아가기
          </button>
        </div>
      </div>
    );
  }

  const handlePurchase = () => {
    setPurchaseSuccess(true);
    setTimeout(() => setPurchaseSuccess(false), 3000);
  };

  const handleSave = () => {
    setSavedToWishlist(true);
    setIsLiked(true);
    setTimeout(() => setSavedToWishlist(false), 2000);
  };

  return (
    <div className="h-full overflow-y-auto bg-[#F8FBF3]">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-white/80 backdrop-blur-sm border-b border-gray-100 px-4 py-3 flex items-center gap-3">
        <button
          onClick={() => navigate("/wishlist")}
          className="p-2 rounded-xl hover:bg-gray-100 transition-colors"
        >
          <ChevronLeft className="w-5 h-5 text-gray-600" />
        </button>
        <h2 className="flex-1 text-sm font-semibold text-gray-800 truncate">{product.name}</h2>
        <button className="p-2 rounded-xl hover:bg-gray-100 transition-colors">
          <Share2 className="w-4 h-4 text-gray-500" />
        </button>
      </div>

      <div className="max-w-2xl mx-auto px-4 py-5 space-y-5">
        {/* Product Image */}
        <motion.div
          initial={{ opacity: 0, scale: 0.96 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.3 }}
          className="relative rounded-3xl overflow-hidden bg-white border border-gray-100 shadow-sm"
        >
          <img
            src={product.image}
            alt={product.name}
            className="w-full aspect-square object-cover"
          />
          {product.badge && (
            <span
              className="absolute top-4 left-4 text-xs font-bold px-3 py-1 rounded-xl text-white shadow-sm"
              style={{ background: product.badgeColor }}
            >
              {product.badge}
            </span>
          )}
          <button
            onClick={() => setIsLiked(!isLiked)}
            className="absolute top-4 right-4 w-10 h-10 bg-white rounded-2xl shadow-md flex items-center justify-center transition-transform hover:scale-110"
          >
            <Heart
              className="w-5 h-5 transition-all"
              style={{
                color: isLiked ? "#EF4444" : "#D1D5DB",
                fill: isLiked ? "#EF4444" : "none",
              }}
            />
          </button>
        </motion.div>

        {/* Product Info */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.1 }}
          className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm"
        >
          <div className="flex items-start justify-between gap-3 mb-3">
            <div>
              <p className="text-sm text-gray-400 mb-1">{product.brand}</p>
              <h1 className="text-gray-900">{product.name}</h1>
            </div>
            <div className="text-right flex-shrink-0">
              <p className="text-xl font-bold text-gray-900">₩{product.price.toLocaleString()}</p>
            </div>
          </div>

          <div className="flex items-center gap-3 mb-4">
            <div className="flex items-center gap-1">
              {[1, 2, 3, 4, 5].map((s) => (
                <Star
                  key={s}
                  className="w-4 h-4"
                  style={{
                    fill: s <= Math.round(product.rating) ? "#F59E0B" : "none",
                    color: s <= Math.round(product.rating) ? "#F59E0B" : "#D1D5DB",
                  }}
                />
              ))}
            </div>
            <span className="text-sm font-semibold text-gray-700">{product.rating}</span>
            <span className="text-sm text-gray-400">({product.reviews.toLocaleString()}개 리뷰)</span>
          </div>

          <div className="flex flex-wrap gap-2 mb-5">
            {product.tags.map((tag) => (
              <span
                key={tag}
                className="text-xs px-3 py-1 rounded-lg font-medium"
                style={{ background: "#E8F5D0", color: "#4A7A1E" }}
              >
                #{tag}
              </span>
            ))}
          </div>

          {/* CTA Buttons */}
          <div className="flex gap-3">
            <button
              onClick={handleSave}
              className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-medium border-2 transition-all duration-200 ${
                savedToWishlist || isLiked
                  ? "border-[#84C13D] text-[#84C13D] bg-[#E8F5D0]"
                  : "border-gray-200 text-gray-600 hover:border-[#84C13D] hover:text-[#84C13D]"
              }`}
            >
              {savedToWishlist ? (
                <>
                  <Check className="w-4 h-4" />
                  저장됨
                </>
              ) : (
                <>
                  <Bookmark className="w-4 h-4" />
                  저장하기
                </>
              )}
            </button>
            <motion.button
              onClick={handlePurchase}
              whileTap={{ scale: 0.97 }}
              className="flex-1 flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-medium text-white shadow-sm transition-all duration-200"
              style={{
                background: purchaseSuccess
                  ? "#10B981"
                  : "linear-gradient(135deg, #84C13D, #6BA32E)",
                boxShadow: purchaseSuccess
                  ? "0 2px 8px rgba(16,185,129,0.3)"
                  : "0 2px 8px rgba(133,193,61,0.3)",
              }}
            >
              {purchaseSuccess ? (
                <>
                  <Check className="w-4 h-4" />
                  구매 완료!
                </>
              ) : (
                <>
                  <ShoppingBag className="w-4 h-4" />
                  구매하기
                </>
              )}
            </motion.button>
          </div>
        </motion.div>

        {/* Service Info */}
        <div className="grid grid-cols-3 gap-3">
          {[
            { icon: Truck, label: "무료 배송", desc: "3만원 이상" },
            { icon: RotateCcw, label: "30일 반품", desc: "무료 반품" },
            { icon: Shield, label: "정품 보장", desc: "100% 정품" },
          ].map((item) => {
            const Icon = item.icon;
            return (
              <div key={item.label} className="bg-white rounded-xl p-3 border border-gray-100 text-center">
                <Icon className="w-5 h-5 mx-auto mb-1.5" style={{ color: "#84C13D" }} />
                <p className="text-xs font-semibold text-gray-700">{item.label}</p>
                <p className="text-[11px] text-gray-400">{item.desc}</p>
              </div>
            );
          })}
        </div>

        {/* Accordion Sections */}
        {[
          {
            id: "desc",
            title: "제품 설명",
            content: (
              <p className="text-sm text-gray-600 leading-relaxed">{product.desc}</p>
            ),
          },
          {
            id: "how",
            title: "사용 방법",
            content: (
              <ol className="space-y-2 text-sm text-gray-600">
                <li className="flex gap-2"><span className="font-bold text-[#84C13D]">01</span> 세안 후 스킨 케어 중 적절한 단계에서 사용</li>
                <li className="flex gap-2"><span className="font-bold text-[#84C13D]">02</span> 적당량을 덜어 얼굴에 고루 펴 바름</li>
                <li className="flex gap-2"><span className="font-bold text-[#84C13D]">03</span> 부드럽게 두드려 흡수 촉진</li>
              </ol>
            ),
          },
          {
            id: "ingre",
            title: "주요 성분",
            content: (
              <div className="flex flex-wrap gap-2">
                {["세라마이드", "히알루론산", "판테놀", "나이아신아마이드", "알란토인"].map((ing) => (
                  <span
                    key={ing}
                    className="text-xs px-3 py-1.5 rounded-xl font-medium"
                    style={{ background: "#F0FAE3", color: "#4A7A1E" }}
                  >
                    {ing}
                  </span>
                ))}
              </div>
            ),
          },
        ].map((section) => (
          <div key={section.id} className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
            <button
              onClick={() => setExpandedSection(expandedSection === section.id ? null : section.id)}
              className="w-full flex items-center justify-between px-5 py-4 text-sm font-semibold text-gray-800 hover:bg-gray-50 transition-colors"
            >
              {section.title}
              <ChevronDown
                className="w-4 h-4 text-gray-400 transition-transform duration-200"
                style={{ transform: expandedSection === section.id ? "rotate(180deg)" : "" }}
              />
            </button>
            {expandedSection === section.id && (
              <div className="px-5 pb-4 border-t border-gray-50">{section.content}</div>
            )}
          </div>
        ))}

        {/* Reviews */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-800">리뷰</h3>
            <div className="flex items-center gap-1">
              <Star className="w-4 h-4 fill-yellow-400 text-yellow-400" />
              <span className="text-sm font-bold text-gray-800">{product.rating}</span>
              <span className="text-sm text-gray-400">({product.reviews.toLocaleString()})</span>
            </div>
          </div>
          <div className="space-y-4">
            {REVIEWS.map((review) => (
              <div key={review.id} className="pb-4 border-b border-gray-50 last:border-0 last:pb-0">
                <div className="flex items-center justify-between mb-1.5">
                  <div className="flex items-center gap-2">
                    <div className="w-7 h-7 rounded-full bg-gray-100 flex items-center justify-center text-xs font-medium text-gray-500">
                      {review.author[0]}
                    </div>
                    <span className="text-xs font-medium text-gray-700">{review.author}</span>
                    <div className="flex">
                      {Array.from({ length: review.rating }).map((_, i) => (
                        <Star key={i} className="w-3 h-3 fill-yellow-400 text-yellow-400" />
                      ))}
                    </div>
                  </div>
                  <span className="text-[11px] text-gray-400">{review.date}</span>
                </div>
                <p className="text-sm text-gray-600 leading-relaxed">{review.content}</p>
                <button className="mt-1.5 text-[11px] text-gray-400 hover:text-[#84C13D] transition-colors">
                  도움됨 {review.helpful}
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
