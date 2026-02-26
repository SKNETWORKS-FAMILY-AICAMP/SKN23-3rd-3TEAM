import { useState } from "react";
import {
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { Droplets, Zap, Eye, Sun, Shield, AlertCircle, TrendingUp, Calendar, ChevronLeft, ChevronRight } from "lucide-react";
import { motion } from "motion/react";

const SKIN_METRICS = [
  { key: "moisture", label: "수분", value: 65, icon: Droplets, color: "#3B82F6", desc: "평균 이하" },
  { key: "oil", label: "피지", value: 72, icon: Zap, color: "#F59E0B", desc: "약간 높음" },
  { key: "pores", label: "모공", value: 60, icon: Eye, color: "#8B5CF6", desc: "보통" },
  { key: "pigment", label: "색소침착", value: 78, icon: Sun, color: "#EC4899", desc: "주의 필요" },
  { key: "elasticity", label: "탄력", value: 82, icon: Shield, color: "#10B981", desc: "양호" },
  { key: "sensitivity", label: "민감도", value: 45, icon: AlertCircle, color: "#EF4444", desc: "매우 낮음" },
];

const RADAR_DATA = [
  { subject: "수분", A: 65, B: 80, fullMark: 100 },
  { subject: "피지조절", A: 72, B: 75, fullMark: 100 },
  { subject: "모공관리", A: 60, B: 70, fullMark: 100 },
  { subject: "탄력", A: 82, B: 78, fullMark: 100 },
  { subject: "미백", A: 58, B: 65, fullMark: 100 },
  { subject: "진정", A: 70, B: 72, fullMark: 100 },
];

const TREND_DATA = [
  { date: "1/25", moisture: 55, elasticity: 78, oil: 80 },
  { date: "2/1", moisture: 58, elasticity: 79, oil: 78 },
  { date: "2/8", moisture: 60, elasticity: 80, oil: 76 },
  { date: "2/15", moisture: 62, elasticity: 81, oil: 74 },
  { date: "2/22", moisture: 65, elasticity: 82, oil: 72 },
];

function MetricBar({ value, color }: { value: number; color: string }) {
  return (
    <div className="w-full bg-gray-100 rounded-full h-2 overflow-hidden">
      <motion.div
        initial={{ width: 0 }}
        animate={{ width: `${value}%` }}
        transition={{ duration: 1, ease: "easeOut", delay: 0.3 }}
        className="h-full rounded-full"
        style={{ background: color }}
      />
    </div>
  );
}

function ScoreGauge({ score }: { score: number }) {
  const circumference = 2 * Math.PI * 54;
  const offset = circumference - (score / 100) * circumference;
  return (
    <div className="relative w-36 h-36">
      <svg className="w-full h-full -rotate-90" viewBox="0 0 120 120">
        <circle cx="60" cy="60" r="54" fill="none" stroke="#E5E7EB" strokeWidth="10" />
        <motion.circle
          cx="60"
          cy="60"
          r="54"
          fill="none"
          stroke="url(#scoreGradient)"
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1.5, ease: "easeOut" }}
        />
        <defs>
          <linearGradient id="scoreGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#85C13D" />
            <stop offset="100%" stopColor="#A8D870" />
          </linearGradient>
        </defs>
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <motion.span
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.8 }}
          className="text-3xl font-bold"
          style={{ color: "#85C13D" }}
        >
          {score}
        </motion.span>
        <span className="text-xs text-gray-400 font-medium">전체 점수</span>
      </div>
    </div>
  );
}

export function AnalysisPage() {
  const [activeTab, setActiveTab] = useState<"current" | "compare">("current");
  const [analysisDate, setAnalysisDate] = useState("2025.02.22");
  const overallScore = 69;

  return (
    <div className="h-full overflow-y-auto bg-[#F8FBF3]">
      <div className="max-w-5xl mx-auto px-4 py-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-gray-900 font-bold">피부 분석 결과</h1>
            <p className="text-sm text-gray-500 mt-0.5">AI가 분석한 나의 피부 상태</p>
          </div>
          <div className="flex items-center gap-2 bg-white rounded-xl px-3 py-2 border border-gray-100 shadow-sm">
            <button className="p-1 hover:text-[#85C13D] transition-colors">
              <ChevronLeft className="w-4 h-4 text-gray-400" />
            </button>
            <div className="flex items-center gap-1.5">
              <Calendar className="w-3.5 h-3.5" style={{ color: "#85C13D" }} />
              <span className="text-xs font-medium text-gray-700">{analysisDate}</span>
            </div>
            <button className="p-1 hover:text-[#85C13D] transition-colors">
              <ChevronRight className="w-4 h-4 text-gray-400" />
            </button>
          </div>
        </div>

        {/* Tab */}
        <div className="flex gap-1 bg-white rounded-xl p-1 border border-gray-100 shadow-sm mb-6 w-fit">
          {[{ id: "current", label: "현재 분석" }, { id: "compare", label: "비교 분석" }].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                activeTab === tab.id ? "text-white shadow-sm" : "text-gray-500 hover:text-gray-700"
              }`}
              style={activeTab === tab.id ? { background: "linear-gradient(135deg, #85C13D, #6BA32E)" } : {}}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {activeTab === "current" ? (
          <div className="space-y-5">
            {/* Score + Type Card */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4 }}
                className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm"
              >
                <h3 className="font-semibold text-gray-800 mb-4">종합 피부 점수</h3>
                <div className="flex items-center gap-6">
                  <ScoreGauge score={overallScore} />
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <span
                        className="px-2.5 py-1 rounded-lg text-xs font-semibold text-white"
                        style={{ background: "#85C13D" }}
                      >
                        복합성 피부
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 leading-relaxed">
                      T존 피지 분비가 활발하고 볼 부위는 수분이 부족한{" "}
                      <strong>수분 부족형 복합성 피부</strong>입니다.
                    </p>
                    <div className="mt-3 flex items-center gap-1.5 text-xs text-[#85C13D]">
                      <TrendingUp className="w-3.5 h-3.5" />
                      지난달 대비 +4점 향상
                    </div>
                  </div>
                </div>
              </motion.div>

              {/* Analysis image */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: 0.1 }}
                className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden"
              >
                <div className="relative h-full min-h-[200px]">
                  <img
                    src="https://images.unsplash.com/photo-1710301496719-11d44e51dbe3?w=600&h=400&fit=crop"
                    alt="Skin analysis"
                    className="w-full h-full object-cover"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent" />
                  <div className="absolute bottom-4 left-4 right-4">
                    <p className="text-white text-sm font-medium">분석 이미지</p>
                    <p className="text-white/70 text-xs">2025.02.22 분석</p>
                  </div>
                  {/* Hotspots */}
                  <div
                    className="absolute top-[35%] left-[48%] w-6 h-6 rounded-full border-2 border-yellow-400 bg-yellow-400/20 animate-pulse"
                    title="피지 분비 감지"
                  />
                  <div
                    className="absolute top-[55%] left-[30%] w-5 h-5 rounded-full border-2 border-blue-400 bg-blue-400/20 animate-pulse"
                    title="수분 부족"
                  />
                </div>
              </motion.div>
            </div>

            {/* Metrics Grid */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.2 }}
              className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm"
            >
              <h3 className="font-semibold text-gray-800 mb-5">피부 지표 상세</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
                {SKIN_METRICS.map((metric, idx) => {
                  const Icon = metric.icon;
                  return (
                    <motion.div
                      key={metric.key}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.3 + idx * 0.08 }}
                      className="flex items-start gap-3 p-3 rounded-xl bg-gray-50"
                    >
                      <div
                        className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
                        style={{ background: metric.color + "20" }}
                      >
                        <Icon className="w-5 h-5" style={{ color: metric.color }} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm font-medium text-gray-700">{metric.label}</span>
                          <span className="text-sm font-bold" style={{ color: metric.color }}>
                            {metric.value}
                          </span>
                        </div>
                        <MetricBar value={metric.value} color={metric.color} />
                        <p className="text-[11px] text-gray-400 mt-1">{metric.desc}</p>
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            </motion.div>

            {/* Radar Chart */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.3 }}
              className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm"
            >
              <h3 className="font-semibold text-gray-800 mb-1">피부 레이더 차트</h3>
              <p className="text-xs text-gray-400 mb-4">현재 vs 이상적 피부 상태 비교</p>
              <ResponsiveContainer width="100%" height={280}>
                <RadarChart data={RADAR_DATA} margin={{ top: 10, right: 30, bottom: 10, left: 30 }}>
                  <PolarGrid stroke="#E5E7EB" />
                  <PolarAngleAxis dataKey="subject" tick={{ fontSize: 12, fill: "#6B7280" }} />
                  <Radar name="현재" dataKey="A" stroke="#85C13D" fill="#85C13D" fillOpacity={0.3} />
                  <Radar name="이상" dataKey="B" stroke="#3B82F6" fill="#3B82F6" fillOpacity={0.15} />
                  <Legend
                    formatter={(value) => <span className="text-xs text-gray-600">{value}</span>}
                  />
                </RadarChart>
              </ResponsiveContainer>
            </motion.div>
          </div>
        ) : (
          <div className="space-y-5">
            {/* Trend Chart */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm"
            >
              <h3 className="font-semibold text-gray-800 mb-1">피부 상태 변화 추이</h3>
              <p className="text-xs text-gray-400 mb-4">최근 30일 피부 지표 변화</p>
              <ResponsiveContainer width="100%" height={260}>
                <LineChart data={TREND_DATA}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" />
                  <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#9CA3AF" }} />
                  <YAxis domain={[40, 100]} tick={{ fontSize: 11, fill: "#9CA3AF" }} />
                  <Tooltip
                    contentStyle={{ borderRadius: "12px", border: "1px solid #E5E7EB", fontSize: "12px" }}
                  />
                  <Legend
                    formatter={(value) => (
                      <span className="text-xs text-gray-600">
                        {value === "moisture" ? "수분" : value === "elasticity" ? "탄력" : "피지"}
                      </span>
                    )}
                  />
                  <Line type="monotone" dataKey="moisture" stroke="#3B82F6" strokeWidth={2} dot={{ r: 4 }} />
                  <Line type="monotone" dataKey="elasticity" stroke="#85C13D" strokeWidth={2} dot={{ r: 4 }} />
                  <Line type="monotone" dataKey="oil" stroke="#F59E0B" strokeWidth={2} dot={{ r: 4 }} />
                </LineChart>
              </ResponsiveContainer>
            </motion.div>

            {/* Before/After */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm"
            >
              <h3 className="font-semibold text-gray-800 mb-5">이전 vs 현재 비교</h3>
              <div className="grid grid-cols-2 gap-4">
                {[
                  { label: "1개월 전 (2025.01.22)", score: 65, badge: "이전" },
                  { label: "현재 (2025.02.22)", score: 69, badge: "현재" },
                ].map((item, idx) => (
                  <div key={idx} className="rounded-xl overflow-hidden border border-gray-100">
                    <div className="relative">
                      <img
                        src="https://images.unsplash.com/photo-1710301496719-11d44e51dbe3?w=400&h=300&fit=crop"
                        alt={item.label}
                        className={`w-full h-48 object-cover ${idx === 0 ? "grayscale-[50%]" : ""}`}
                      />
                      <span
                        className="absolute top-3 left-3 text-xs font-semibold px-2.5 py-1 rounded-lg text-white"
                        style={{ background: idx === 1 ? "#85C13D" : "#6B7280" }}
                      >
                        {item.badge}
                      </span>
                    </div>
                    <div className="p-3">
                      <p className="text-xs text-gray-400 mb-1">{item.label}</p>
                      <div className="flex items-center gap-2">
                        <span className="text-xl font-bold" style={{ color: idx === 1 ? "#85C13D" : "#6B7280" }}>
                          {item.score}점
                        </span>
                        {idx === 1 && (
                          <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-[#E8F5D0]" style={{ color: "#4A7A1E" }}>
                            +4점 ↑
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>

            {/* Change Summary */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm"
            >
              <h3 className="font-semibold text-gray-800 mb-4">변화 요약</h3>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                {[
                  { label: "수분", prev: 58, curr: 65, color: "#3B82F6" },
                  { label: "탄력", prev: 79, curr: 82, color: "#10B981" },
                  { label: "피지", prev: 80, curr: 72, color: "#F59E0B" },
                  { label: "모공", prev: 55, curr: 60, color: "#8B5CF6" },
                  { label: "색소침착", prev: 82, curr: 78, color: "#EC4899" },
                  { label: "민감도", prev: 40, curr: 45, color: "#EF4444" },
                ].map((item) => {
                  const diff = item.curr - item.prev;
                  return (
                    <div key={item.label} className="p-3 rounded-xl bg-gray-50">
                      <p className="text-xs text-gray-500 mb-1">{item.label}</p>
                      <div className="flex items-end gap-1.5">
                        <span className="font-bold text-gray-800">{item.curr}</span>
                        <span
                          className="text-xs font-semibold mb-0.5"
                          style={{ color: diff >= 0 ? "#85C13D" : "#EF4444" }}
                        >
                          {diff >= 0 ? `+${diff}` : diff}
                        </span>
                      </div>
                      <MetricBar value={item.curr} color={item.color} />
                    </div>
                  );
                })}
              </div>
            </motion.div>
          </div>
        )}
      </div>
    </div>
  );
}
